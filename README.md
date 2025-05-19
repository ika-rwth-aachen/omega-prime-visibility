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


# Notice

> [!IMPORTANT]
> The project is open-sourced and maintained by the [**Institute for Automotive Engineering (ika) at RWTH Aachen University**](https://www.ika.rwth-aachen.de/).
> We cover a wide variety of research topics within our [*Vehicle Intelligence & Automated Driving*](https://www.ika.rwth-aachen.de/en/competences/fields-of-research/vehicle-intelligence-automated-driving.html) domain.
> If you would like to learn more about how we can support your automated driving or robotics efforts, feel free to reach out to us!
> :email: ***opensource@ika.rwth-aachen.de***