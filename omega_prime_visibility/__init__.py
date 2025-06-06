import visilibity as vis
from shapely.strtree import STRtree
import shapely
import polars as pl
import numpy as np
import warnings
from collections import defaultdict
from tqdm.auto import tqdm
import omega_prime


EPSILON = 1e-6

__all__ = ["get_visibility_df", "get_visibility_df_for_frame", "visibility"]


def unit_vector(vector: np.ndarray):
    """Returns the unit vector of the vector."""
    norm = np.linalg.norm(vector)
    return vector / norm


def angle_between(v1, v2):
    """
    compute angle between two vectors
    """
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))


def polar_angle(coordinate, origin):
    """
    returns angle in polar coordinates
    0 at pos x-axis
    [0, +pi] from pos x-axis over pos y-axis to neg x-axis
    [0, -pi] from pos x-axis over neg y-axis to neg x-axis
    """
    return np.arctan2(coordinate[1] - origin[1], coordinate[0] - origin[0])


def get_visibility_df_for_frame(
    df: pl.DataFrame,
    ego_idx: int,
    frame: int,
    static_occluder_polys: None | list[shapely.Geometry] = None,
    epsilon: float = EPSILON,
) -> pl.DataFrame:
    if static_occluder_polys is None:
        static_occluder_polys = []

    poly_df = df.filter(frame=frame)["idx", "x", "y", "polygon"]

    ego_df = poly_df.filter(idx=ego_idx)
    other_df = poly_df.filter(pl.col("idx") != ego_idx)
    ego_bbx = ego_df["polygon"].first()

    convex_hull = shapely.convex_hull(shapely.MultiPolygon(list(poly_df["polygon"]) + static_occluder_polys)).buffer(5)
    visenv = vis.Environment(
        [
            vis.Polygon([vis.Point(x, y) for x, y in p.boundary.coords])
            for p in [convex_hull] + [p for p in other_df["polygon"]] + static_occluder_polys
        ]
    )
    npq = np.asarray(ego_df["x", "y"])[0]
    observer = vis.Point(*npq)
    observer.snap_to_boundary_of(visenv, epsilon)
    observer.snap_to_vertices_of(visenv, epsilon)

    # Obtein the visibility polygon of the 'observer' in the environmente
    # previously define
    visible = vis.Visibility_Polygon(observer, visenv, epsilon)
    vis_points = np.array([(p.x(), p.y()) for p in [visible[i] for i in range(visible.n())]])
    # skip every second half edge, to prevent duplicates
    visible_edge = shapely.LineString(vis_points).buffer(epsilon)
    bbx_str_tree = STRtree(list(other_df["polygon"]) + static_occluder_polys)
    bbx_str_tree_idx2object_idx = other_df["idx"]
    bbx_str_tree_idx2static_idx = {other_df.height + i: i for i, _ in enumerate(static_occluder_polys)}

    visibility = {}
    occluders = defaultdict(list)
    static_occluders = defaultdict(list)
    for i, bbx in other_df["idx", "polygon"].iter_rows():
        # initialize clockwise first and last points with arbitrary points
        first = next(
            iter(bbx.boundary.coords)
        )  # point of bounding box that lies first in clockwise order from pos x-axis
        last = first  # point of bounding box that lies last in clockwise order from pos x-axis
        visible_angle = 0

        # define negative x-axis with origin in q
        y_axis_negative_part = shapely.LineString([npq, np.array([npq[0] - 1e5, npq[1]])])
        # check if bbx intersects with negative x-axis
        # (as angle changes from -pi to +pi at negative x-axis, that case needs special treatment for sorting)
        if y_axis_negative_part.intersects(bbx):
            invert = True
        else:
            invert = False

        # search for clockwise first and last points of bounding box
        # angle is given in polar coordinates with 0 at pos x-axis and counterclockwise increase
        # angle range [-pi, pi]
        for a, b in zip(
            bbx.boundary.coords,
            list(bbx.boundary.coords[1:]) + list(bbx.boundary.coords[:1]),
        ):
            # get first and last point
            for point in [a, b]:
                angle = polar_angle(point, npq)
                if not invert:
                    if angle < polar_angle(last, npq):
                        last = point
                    elif angle > polar_angle(first, npq):
                        first = point
                else:  # bbx is overlapping negative x-axis (=> sign change from first to last point of bbx)
                    if angle < 0 <= polar_angle(first, npq):
                        first = point
                    if polar_angle(first, npq) < angle < 0 and angle:
                        first = point
                    if polar_angle(last, npq) < 0 <= angle:
                        last = point
                    elif 0 <= angle < polar_angle(last, npq):
                        last = point

            # for every visible segment that intersects with bounding box
            shapley_bbx_segment = shapely.LineString([a, b])
            intersections = shapley_bbx_segment.intersection(visible_edge)
            if not hasattr(intersections, "geoms"):
                intersections = [intersections]
            else:
                intersections = intersections.geoms
            for inter in intersections:
                if inter.length > 0:
                    vec = np.array(inter.coords) - npq
                    visible_angle += angle_between(*vec)

        # compute angle between first and last points of bounding box from q
        max_visible_angle = angle_between(first - npq, last - npq)
        if max_visible_angle == 0:  # prevent division by 0
            visibility[i] = 0
        else:
            visibility[i] = float(round(visible_angle / max_visible_angle, 2))  # round to 2 digits
        # just to be sure
        if visibility[i] > 1:
            if ego_bbx.intersects(bbx):
                visibility[i] = 1
            else:
                # visibility[i] = 1
                warnings.warn(
                    f"WARNING: Visibility value larger than one: vis={visibility[i]}",
                    RuntimeWarning,
                )
        # compute occluding objects
        if visibility[i] < 1:
            field_of_view = shapely.convex_hull(shapely.MultiPolygon([bbx, shapely.Point(*npq).buffer(0.01)]))
            for occlusion_candidate in bbx_str_tree.query(field_of_view, predicate="intersects"):
                # object lies inside the field of view from ego to current bbx
                try:
                    occluder_id = bbx_str_tree_idx2object_idx[int(occlusion_candidate)]
                    if i != occluder_id and occluder_id != ego_idx:
                        occluders[i].append(occluder_id)
                except IndexError:
                    occluder_id = bbx_str_tree_idx2static_idx[int(occlusion_candidate)]
                    static_occluders[i].append(occluder_id)

    visibility_df = pl.DataFrame(
        {
            "frame": [frame for _ in range(other_df.height)],
            "idx": other_df["idx"],
            "occluder_idxs": pl.Series(values=[occluders.get(idx, []) for idx in other_df["idx"]], dtype=list[int]),
            "static_occluder_idxs": pl.Series(
                values=[static_occluders.get(idx, []) for idx in other_df["idx"]], dtype=list[int]
            ),
            "visibility": pl.Series(values=[visibility.get(idx, None) for idx in other_df["idx"]], dtype=float),
        }
    )
    return visibility_df


def get_visibility_df(
    df: pl.DataFrame,
    ego_idx: int,
    static_occluder_polys: None | list[shapely.Geometry] = None,
    epsilon: float = EPSILON,
    hide_progress: bool | None = False,
) -> pl.DataFrame:
    res = pl.concat(
        [
            get_visibility_df_for_frame(df, ego_idx, frame=f, static_occluder_polys=static_occluder_polys)
            for f in tqdm(df.filter(idx=ego_idx)["frame"].unique(), disable=hide_progress, leave=False, desc='Compute Visibility')
        ]
    ).join(df['frame','total_nanos','idx'], on=['frame','idx'])['frame','total_nanos','idx','occluder_idxs','static_occluder_idxs','visibility']
    return res


@omega_prime.metrics.metric(computes_properties=["visibility"])
def visibility(
    df: pl.LazyFrame,
    ego_idx: int,
    static_occluder_polys: None | list[shapely.Geometry] = None,
    epsilon: float = EPSILON,
) -> pl.LazyFrame:
    eager_df = df["idx", "x", "y", "polygon"].collect()
    vis_df = get_visibility_df(eager_df, ego_idx, static_occluder_polys, epsilon, show_porgress=False)
    return df, {"visibility": pl.LazyFrame(vis_df)}

metrics = [
    visibility
]