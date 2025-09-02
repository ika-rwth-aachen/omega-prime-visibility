# Omega-Prime-Visibility

This packages uses [VisiLibity1](https://karlobermeyer.github.io/VisiLibity1/) through [visilibity](https://pypi.org/project/VisiLibity/) (LGPL) to comptue the visibility of MovingObjects of [omega-prime](https://github.com/ika-rwth-aachen/omega-prime)-Recordings. For every object it computes the visibilty as a float (`1.0` for fully visible and `0.0` for not visible) (assuming 2D-brids-eye-view geometries) from the point of view of one object (assumed as a point in the center of the object). In addition the objects occluding the view (occluders) are computed.

This package also provides the computation of visibility as an omega-prime [Metric](https://github.com/ika-rwth-aachen/omega-prime/blob/main/tutorial_metrics.ipynb): `from omega_prime_visibility import visibility`.

The example file [highway_merge.mcap](./highway_merge.mcap) is taken from [omega-prime](https://github.com/ika-rwth-aachen/omega-prime) and derived from [esmini](https://github.com/esmini/esmini) and is under MPL-2.0 license.

## License
This python package is distributed under MIT license but the linked libraries [visilibity](https://pypi.org/project/VisiLibity/) and [VisiLibity1](https://karlobermeyer.github.io/VisiLibity1/) are under the GNU Lesser General Public License (LGPL).

## Requirements
You need to have installed `swig`, `boost` and `cython` to be able to install [visilibity](https://pypi.org/project/VisiLibity/)

On windows you need to additonally install Buildtools:
1. Download [Buildtools für Visual Studio 2022](https://aka.ms/vs/17/release/vs_BuildTools.exe)
2. Select `C++ Tools for Linux Development` and install

## Installation
`pip install omega-prime-visibility`

## Usage
See [./tutorial.ipynb](./tutorial.ipynb) for detailed instructions.


```python
from omega_prime_visibility import get_visibility_df
import omega_prime
import shapely

r = omega_prime.Recording.from_file('highway_merge.mcap', compute_polygons=True)

obstruction_poly = shapely.Polygon([
    [-220,10],
    [-120,10],
    [-120,-0],
    [-220,-0],
])
df = get_visibility_df(r._df, ego_idx=0, static_occluder_polys=[obstruction_poly])
```

returns

|   frame |   idx | occluder_idxs   | static_occluder_idxs   |   visibility |
|--------:|------:|:----------------|:-----------------------|-------------:|
|       0 |     1 | []              | [0]                    |         0.42 |
|       0 |     2 | []              | [0]                    |         0    |
|       0 |     3 | []              | [0]                    |         0    |
|       0 |     4 | []              | [0]                    |         0    |
|       0 |     5 | [3]             | [0]                    |         0    |
|       1 |     1 | []              | [0]                    |         0.53 |
|       1 |     2 | []              | [0]                    |         0    |
|       1 |     3 | []              | [0]                    |         0    |
|       1 |     4 | []              | [0]                    |         0    |
|       1 |     5 | [3]             | [0]                    |         0    |
|       2 |     1 | []              | [0]                    |         0.63 |
|       2 |     2 | []              | [0]                    |         0    |
|       2 |     3 | []              | [0]                    |         0    |
|       2 |     4 | []              | [0]                    |         0    |
|       2 |     5 | [3]             | [0]                    |         0    |
|       3 |     1 | []              | [0]                    |         0.74 |
|     ... |   ... | ...             | ...                    |         ...  |
|     432 |     3 | []              | []                     |         1    |
|     432 |     4 | [1 2 5]         | []                     |         0    |
|     432 |     5 | [1 2]           | []                     |         0    |

# Algorithm
For every point in time compute a visibility for every object from the perspective of an ego vehicle based on 2D-brids-eye-view geometry:

1. Assume point of obersvation to be the centerpoint of the polygon of the ego vehicle
2. Take polygons of all other objects and create visibility polygon using [VisiLibity1](https://karlobermeyer.github.io/VisiLibity1/) through [PyVisiLibity](https://github.com/tsaoyu/PyVisiLibity).
3. Create `shapely.STRTree` from the same polygons
4. For every object we want the visibilty for:
    1. Compute the angle range of the object from the perspective of the ego: e.g., The vectors from the perspective point to all points of the polygon have a angle between 90° and 100°. This give a maximum viewable angle-range of 10°.
    2. Compute the visible sections of the polygon by intersecting the polygon with the visibility polygon (speed up by using the STRTree)
    3. Compute the angle-range of all visibile segments of the polygon: e.g., `[90°,92°] and [98°-100°]` are the resulting ranges. This gives a total viewable angle range of `2°+2°=4°`
    4. Divide the viewable angle range by the maximum angle range resulting in the visibility between 0 and 1: e.g., `4°/10°=0.4`.
    4. Create the convex hull of the polygon and the persepctive point and find all objects that are interesecting this hull. These are classified as the occluders. 


# Notice

> [!IMPORTANT]
> The project is open-sourced and maintained by the [**Institute for Automotive Engineering (ika) at RWTH Aachen University**](https://www.ika.rwth-aachen.de/).
> We cover a wide variety of research topics within our [*Vehicle Intelligence & Automated Driving*](https://www.ika.rwth-aachen.de/en/competences/fields-of-research/vehicle-intelligence-automated-driving.html) domain.
> If you would like to learn more about how we can support your automated driving or robotics efforts, feel free to reach out to us!
> :email: ***opensource@ika.rwth-aachen.de***