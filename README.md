# pygemc

[![Tests][tests-badge]][tests]
[![Python][python-badge]][pyproject]
[![PyPI][pypi-badge]][pypi]
[![License: GEMC][license-badge]][license]
[![GEMC documentation][docs-badge]][docs]

`pygemc` is the Python API used by [GEMC](https://github.com/gemc/src) to define detector geometry, materials, optical properties, mirrors, geometry variations, and lightweight output-analysis workflows. It lets users build GEMC databases with Python scripts, preview geometry with PyVista, and inspect GEMC CSV or ROOT output without writing C++.

The package is installed as part of the GEMC source build and can also be developed as a standalone Python project.

## Features

- Python classes for GEMC geometry and material databases
- `GVolume` helpers for common Geant4 solids such as boxes, tubes, cones, and trapezoids
- `GMaterial` helpers for chemical formulas, fractional-mass mixtures, and optical/scintillation properties
- `GConfiguration` run, variation, factory, SQLite, ASCII, and PyVista configuration handling
- `autogeometry()` convenience setup for detector scripts
- SQLite and ASCII database output
- PyVista rendering, interactive Qt display, and VTK.js `.vtksz` export for geometry inspection and documentation
- `gemc-system-template` CLI for generating ready-to-run detector systems
- Python code snippets for supported Geant4 solid constructors
- `gemc-analyzer` CLI for summarizing and plotting GEMC CSV or ROOT output
- Unit conversion helpers for length, angle, time, and energy strings
- Pytest suite that does not require a compiled `gemc` binary

## Installation

Choose the installation path based on what you need:

- Use PyPI for Python geometry building, PyVista previews, and output analysis without the compiled `gemc` simulator.
- Build [GEMC from source](https://gemc.github.io/home/installation/#build-and-install-gemc-from-source) for the full Geant4 simulation executable and the bundled `pygemc` Python environment.
- Use the development install when you are editing `pygemc` itself.

Use a Python virtual environment for direct `pip` installs:

```shell
python3 -m venv ~/venv/pygemc
source ~/venv/pygemc/bin/activate
python -m pip install --upgrade pip
```

### Stable PyPI Install

Install [`pygemc` from PyPI](https://pypi.org/project/pygemc/) with:

```shell
python -m pip install pygemc
```

Update an existing PyPI installation with:

```shell
python -m pip install --upgrade pygemc
```

Optional ROOT-file analysis dependencies:

```shell
python -m pip install "pygemc[root]"
```

Update with optional ROOT-file analysis dependencies enabled:

```shell
python -m pip install --upgrade "pygemc[root]"
```

### Development Snapshot

Install the moving GitHub `dev` prerelease with:

```shell
python -m pip install "pygemc @ git+https://github.com/gemc/pygemc.git@dev"
```

Update the GitHub `dev` snapshot with:

```shell
python -m pip install --upgrade --force-reinstall "pygemc @ git+https://github.com/gemc/pygemc.git@dev"
```

Use this when you need the latest development version before the next stable PyPI release.

### Local Clone Development Install

Use this when you are editing `pygemc` from a local clone:

```shell
git clone https://github.com/gemc/pygemc.git
cd pygemc
python -m pip install -e ".[dev]"
```

Optional ROOT-file analysis dependencies for local development:

```shell
python -m pip install -e ".[dev,root]"
```

The package requires Python 3.10 or newer and depends on NumPy, VTK, PyVista, PyVistaQt, PyQt6, pandas, and matplotlib.

### Installed with GEMC

When GEMC is built from source, the parent Meson project installs `pygemc` into the GEMC Python environment at `<prefix>/python_env`. After adding `<prefix>/bin` and `<prefix>/python_env/bin` to `PATH`, the simulator and Python tools are available:

```shell
gemc -v
gemc-system-template --help
gemc-analyzer --help
```

## Quickstart

Create a detector template:

```shell
gemc-system-template -s counter
cd counter
./counter.py
```

The generated system contains:

| File | Purpose |
| --- | --- |
| `counter.py` | Main geometry-builder script |
| `geometry.py` | Example volumes, including a flux detector |
| `materials.py` | Example methane-gas material |
| `counter.yaml` | GEMC steering card |
| `README.md` | Placeholder notes for the generated detector |

Run with PyVista visualization:

```shell
./counter.py -pv
```

Export a VTK.js scene:

```shell
./counter.py -pvvtk counter -pvz 0.25
```

Run the generated simulation with GEMC when the compiled `gemc` executable is available:

```shell
gemc counter.yaml
```

Analyze output:

```shell
gemc-analyzer counter_t0_digitized.csv totEdep --kind csv --bins 50
```

## Geometry API

Typical geometry scripts create a configuration and publish volumes/materials to it:

```python
from pygemc import GMaterial, GVolume, autogeometry

cfg = autogeometry("examples", "counter")

gas = GMaterial("methaneGas")
gas.description = "methane gas CH4 0.000667 g/cm3"
gas.density = 0.000667
gas.addNAtoms("C", 1)
gas.addNAtoms("H", 4)
gas.publish(cfg)

flux = GVolume("flux_box")
flux.description = "air flux box"
flux.make_box(40.0, 40.0, 2.0)
flux.set_position(0, 0, 100)
flux.material = "G4_AIR"
flux.color = "3399FF"
flux.style = 1
flux.digitization = "flux"
flux.set_identifier("box", 2)
flux.publish(cfg)
```

Common command-line options accepted by geometry scripts:

| Option | Purpose |
| --- | --- |
| `-f`, `--factory` | Select `sqlite` or `ascii` output |
| `-v`, `--variation` | Select the geometry variation |
| `-r`, `--run` | Select the run number |
| `-sql`, `--dbhost` | Select the SQLite file path |
| `-pv` | Show a PyVista window |
| `-pvb` | Show a PyVistaQt background plotter |
| `-pvvtk` | Export a VTK.js `.vtksz` scene |
| `-pvz` | Set the VTK.js export zoom |

## PyVista Visualization

PyVista support is central to `pygemc`: geometry scripts can display the detector as they build it, open an interactive Qt viewer, or export a `.vtksz` scene that can be published in documentation.

<!-- PyVista gallery setting: edit width="300" height="300" below to resize all thumbnails. -->
| B1 | B2 |
| --- | --- |
| <a href="https://gemc.github.io/home/assets/vtkjs-viewer.html?fileURL=https://gemc.github.io/home/assets/images/examples/b1/b1.vtksz"><img src="https://gemc.github.io/home/assets/images/examples/b1/geometry.png" alt="B1 PyVista geometry" width="300" height="300"></a> | <a href="https://gemc.github.io/home/assets/vtkjs-viewer.html?fileURL=https://gemc.github.io/home/assets/images/examples/b2/b2.vtksz"><img src="https://gemc.github.io/home/assets/images/examples/b2/geometry.png" alt="B2 PyVista geometry" width="300" height="300"></a> |
| Materials | Simple Flux |
| <a href="https://gemc.github.io/home/assets/vtkjs-viewer.html?fileURL=https://gemc.github.io/home/assets/images/examples/materials/material.vtksz"><img src="https://gemc.github.io/home/assets/images/examples/materials/geometry.png" alt="Materials PyVista geometry" width="300" height="300"></a> | <a href="https://gemc.github.io/home/assets/vtkjs-viewer.html?fileURL=https://gemc.github.io/home/assets/images/examples/simple_flux/simple_flux.vtksz"><img src="https://gemc.github.io/home/assets/images/examples/simple_flux/geometry.png" alt="Simple Flux PyVista geometry" width="300" height="300"></a> |

Open the linked interactive PyVista scenes generated from the GEMC examples.

GitHub README pages cannot embed `.vtksz` files directly, so the preview image links to the hosted VTK.js viewer.

## Command-Line Tools

### `gemc-system-template`

Generate a detector skeleton:

```shell
gemc-system-template -s counter
```

List supported solid snippets:

```shell
gemc-system-template -sl
```

Print a volume-construction snippet:

```shell
gemc-system-template -gv G4Box
```

Write a snippet to a file:

```shell
gemc-system-template -gv G4Tubs -write_to geometry.py -geo_sub build_tube
```

### `gemc-analyzer`

Summarize an output file:

```shell
gemc-analyzer counter_t0_digitized.csv --kind csv
```

Plot a variable:

```shell
gemc-analyzer counter_t0_digitized.csv totEdep --kind csv --bins 50
```

Save a figure without opening a GUI:

```shell
gemc-analyzer out.root E --kind root --detector flux --save energy.png
```

Analyzer inputs:

- CSV output files or CSV root names
- ROOT files when `pygemc[root]` dependencies are installed
- Digitized and true-information data streams

## Tests

Run the standalone Python tests:

```shell
pytest
pytest tests/test_cli.py
pytest tests/test_geometry.py
pytest -v
pytest -k "sqlite"
```

The tests cover CLI behavior and geometry database generation. They intentionally do not require Geant4 or a compiled `gemc` executable; full simulation tests live in the parent GEMC Meson build.

## Project Layout

| Path | Purpose |
| --- | --- |
| `src/pygemc/api/` | Geometry, materials, units, SQLite output, PyVista support, and templates |
| `src/pygemc/analyzer/` | CSV/ROOT readers, plotting, and analyzer CLI |
| `tests/` | Standalone pytest suite |
| `releases/` | Release notes |
| `pyproject.toml` | Python packaging metadata and console scripts |
| `meson.build` | Meson subproject integration used by GEMC |

## Documentation

- [GEMC homepage](https://gemc.github.io/home/)
- [Python API overview](https://gemc.github.io/home/documentation/api/pyvista_api.html)
- [Quickstart](https://gemc.github.io/home/documentation/quickstart/)
- [Examples](https://gemc.github.io/home/examples/)
- [GEMC source repository](https://github.com/gemc/src)

## Contributing

Keep patches focused and run the relevant pytest targets before opening a pull request. If a change affects the integrated GEMC build, also run the parent repository Meson tests for the affected examples or modules.

## License

`pygemc` is distributed under the GEMC Software License, the same license used by the main GEMC source repository. See [`LICENSE.md`](LICENSE.md).

[tests]: https://github.com/gemc/pygemc/actions/workflows/pygemc_tests.yml
[tests-badge]: https://github.com/gemc/pygemc/actions/workflows/pygemc_tests.yml/badge.svg
[python-badge]: https://img.shields.io/badge/python-3.10%2B-blue.svg
[pypi]: https://pypi.org/project/pygemc/
[pypi-badge]: https://img.shields.io/pypi/v/pygemc.svg?cacheSeconds=300
[license]: LICENSE.md
[license-badge]: https://img.shields.io/badge/license-GEMC-blue.svg
[docs]: https://gemc.github.io/home/
[docs-badge]: https://img.shields.io/badge/docs-gemc.github.io-blue.svg
[pyproject]: pyproject.toml
