# pygemc

[![Tests][tests-badge]][tests]
[![Python][python-badge]][pyproject]
[![PyPI][pypi-badge]][pypi]
[![License: GEMC][license-badge]][license]
[![GEMC documentation][docs-badge]][docs]

`pygemc` is the Python API used by [GEMC](https://github.com/gemc/src) to define detector geometry, materials, optical properties, mirrors, 
and lightweight output-analysis workflows. It lets users build GEMC databases with Python scripts, preview geometry 
with PyVista, and inspect GEMC CSV or ROOT output without writing C++.

The package is installed with pip or as part of the GEMC source build.

## Features

- Python classes for GEMC geometry and material databases
- `GVolume` helpers for common Geant4 solids such as boxes, tubes, cones, and trapezoids
- `GVolume.g4placement_type` to select the `G4Transform3D` active or passive constructor
- `GMaterial` helpers for chemical formulas, fractional-mass mixtures, and optical/scintillation properties
- `GConfiguration` run, variation, factory, SQLite, ASCII, and PyVista configuration handling
- `autogeometry()` convenience setup for detector scripts
- SQLite and ASCII database output
- PyVista rendering, interactive Qt display, and VTK.js `.vtksz` export for geometry inspection and documentation
- `gemc-system-template` CLI for generating ready-to-run detector systems
- Python code snippets for supported Geant4 solid constructors
- `gemc-sqlite` CLI for creating and inspecting GEMC SQLite database files
- `gemc-analyzer` CLI for summarizing and plotting GEMC CSV or ROOT output
- Unit conversion helpers for length, angle, time, and energy strings
- Pytest suite that does not require a compiled `gemc` binary

<br/>

# Installation

## Stable PyPI Install

Use a Python virtual environment for direct `pip` installs. 
On macOS with Homebrew use `/opt/homebrew/bin/python3` to ensure the correct interpreter is used:

```shell
/opt/homebrew/bin/python3 -m venv ~/venv/pygemc
source ~/venv/pygemc/bin/activate
python -m pip install --upgrade pip
```

Install [`pygemc` from PyPI](https://pypi.org/project/pygemc/) with:

```shell
python -m pip install pygemc
```
Optional ROOT-file analysis dependencies:

```shell
python -m pip install "pygemc[root]"
```


## Install with GEMC

When GEMC is built from source, pygemc available in your scripts without 
any activation step or separate pip install and gemc and Python tools are available:

```shell
gemc -v
gemc-system-template --help
gemc-sqlite --help
gemc-analyzer --help
```

<br/>

# Quickstart

Create a detector template:

```shell
gemc-system-template -s counter
cd counter
./counter.py
```

The generated system contains:

| File           | Purpose                                      |
| -------------- | -------------------------------------------- |
| `counter.py`   | Main geometry-builder script                 |
| `geometry.py`  | Example volumes, including a flux detector   |
| `materials.py` | Example methane-gas material                 |
| `counter.yaml` | GEMC steering card                           |
| `README.md`    | Placeholder notes for the generated detector |

Run with PyVista visualization:

```shell
./counter.py -pv
```

Export a VTK.js scene:

```shell
./counter.py -pvvtk counter -pvz 0.25
```

Use a light flat background for documentation exports:

```shell
./counter.py -pvvtk counter -pvbg "0.92 0.92 0.98" -pvbgt none
```

Run the generated simulation with GEMC when the compiled `gemc` executable is available:

```shell
gemc counter.yaml
```

Analyze output:

```shell
gemc-analyzer counter_t0_digitized.csv totEdep --kind csv --bins 50
```

The quantities available to plot are the numeric columns of the loaded file, so they are only known after the
data is read — they do not appear in `--help`. Run the analyzer without a variable to print the summary and the
`plottable <stream>: ...` list for each stream, then pick a name from that list:

```shell
gemc-analyzer counter_t0_digitized.csv --kind csv
```

<br/>

# Geometry API

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

## Placement convention

`GVolume.g4placement_type` selects which Geant4 placement convention GEMC should use for a volume:

| Value     | Meaning                                                                                  |
| --------- | ---------------------------------------------------------------------------------------- |
| `active`  | Default; uses `G4Transform3D(rotation, translation)`                                     |
| `passive` | Uses `G4PVPlacement(rotation, translation, ...)`, matching GEMC2/clas12Tags conventions |

Most new GEMC3 geometry can use the default `active` convention. Detector systems ported from GEMC2 that rely on
frame rotations should set:

```python
gvolume.g4placement_type = "passive"
```

This field is written to SQLite geometry databases. Existing SQLite databases are upgraded with the missing
column when a geometry script publishes new rows.

Common command-line options accepted by geometry scripts:

| Option              | Purpose                                                                       |
| ------------------- | ----------------------------------------------------------------------------- |
| `-f`, `--factory`   | Select `sqlite` or `ascii` output                                             |
| `-v`, `--variation` | Select the geometry variation                                                 |
| `-r`, `--run`       | Select the run number                                                         |
| `-sql`, `--dbhost`  | Select the SQLite file path                                                   |
| `-pv`               | Show a PyVista window                                                         |
| `-pvb`              | Show a PyVistaQt background plotter                                           |
| `-pvvtk`            | Export a VTK.js `.vtksz` scene                                                |
| `-pvz`              | Set the VTK.js export zoom                                                    |
| `-pvbg`             | Set the PyVista background color as a name, hex string, or `r g b` triple    |
| `-pvbgt`            | Set the optional PyVista top gradient color; use `none` for a flat background |
| `--read-yaml`       | Read `g4camera` direction and `g4view.background` settings from a GEMC YAML   |

## PyVista Visualization

PyVista support is central to `pygemc`: geometry scripts can display the detector as they build it,
open an interactive Qt viewer, or export a `.vtksz` scene that can be published in documentation.

<table>
  <tr>
    <td>
      <a href="https://gemc.github.io/home/assets/vtkjs-viewer.html?fileURL=/home/assets/images/examples/b1/b1.vtksz"
         target="_blank" rel="noopener noreferrer">
        <img src="https://gemc.github.io/home/assets/images/examples/b1/gemc_view.png"
             alt="B1 PyVista" width="180"><br>
        B1
      </a>
    </td>
    <td>
      <a href="https://gemc.github.io/home/assets/vtkjs-viewer.html?fileURL=/home/assets/images/examples/b2/b2.vtksz"
         target="_blank" rel="noopener noreferrer">
        <img src="https://gemc.github.io/home/assets/images/examples/b2/gemc_view.png"
             alt="B2 PyVista" width="180"><br>
        B2
      </a>
    </td>
  </tr>
  <tr>
    <td>
      <a href="https://gemc.github.io/home/assets/vtkjs-viewer.html?fileURL=/home/assets/images/examples/materials/material.vtksz"
         target="_blank" rel="noopener noreferrer">
        <img src="https://gemc.github.io/home/assets/images/examples/materials/gemc_view.png"
             alt="Materials PyVista" width="180"><br>
        Materials
      </a>
    </td>
    <td>
      <a href="https://gemc.github.io/home/assets/vtkjs-viewer.html?fileURL=/home/assets/images/examples/scintillator_barrel/scintillator_barrel.vtksz"
         target="_blank" rel="noopener noreferrer">
        <img src="https://gemc.github.io/home/assets/images/examples/scintillator_barrel/gemc_view.png"
             alt="Scintillator Barrel PyVista" width="180"><br>
        Scintillator Barrel
      </a>
    </td>
  </tr>
</table>

Open the linked interactive PyVista scenes generated from the GEMC examples.

GitHub README pages cannot embed `.vtksz` files directly, so the preview image links to the hosted VTK.js viewer.

## Command-Line Tools

<table>
  <thead>
    <tr>
      <th>Command</th>
      <th>What it does</th>
    </tr>
  </thead>
  <tbody>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-system-template -s counter</code></td>
      <td>Generate a detector skeleton named <code>counter</code>.</td>
    </tr>
    <tr>
      <td><code>gemc-system-template -sl</code></td>
      <td>List supported Geant4 solid snippets.</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-system-template -gv G4Box</code></td>
      <td>Print a volume-construction snippet for a <code>G4Box</code>.</td>
    </tr>
    <tr>
      <td><code>gemc-system-template -gv G4Tubs -write_to geometry.py -geo_sub build_tube</code></td>
      <td>Write a <code>G4Tubs</code> snippet to <code>geometry.py</code>.</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-sqlite -n mydetector.sqlite</code></td>
      <td>Create a new SQLite database with the GEMC geometry and materials schema.</td>
    </tr>
    <tr>
      <td><code>gemc-sqlite -sql mydetector.sqlite -sv</code></td>
      <td>Open an existing database and list its volumes.</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-sqlite -sql mydetector.sqlite -sm</code></td>
      <td>Open an existing database and list its materials.</td>
    </tr>
    <tr>
      <td>
        <code>gemc-sqlite -sql mydetector.sqlite -sv -ef examples -vf default -sf counter -rf 1</code>
      </td>
      <td>Filter listed volumes by experiment, variation, system, and run number.</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td><code>gemc-analyzer counter_t0_digitized.csv --kind csv</code></td>
      <td>Summarize a GEMC CSV output file and list the plottable quantities per stream.</td>
    </tr>
    <tr>
      <td><code>gemc-analyzer counter_t0_digitized.csv totEdep --kind csv --bins 50</code></td>
      <td>Plot a digitized variable with 50 bins.</td>
    </tr>
    <tr style="background-color: #f6f8fa;">
      <td>
        <code>
          gemc-analyzer counter_t0_true_info.csv --kind csv --data true_info --plot yvsx --xlim -20 20
          --ylim -20 20
        </code>
      </td>
      <td>Plot true hit positions in the y-vs-x plane.</td>
    </tr>
    <tr>
      <td><code>gemc-analyzer out.root E --kind root --detector flux --save energy.png</code></td>
      <td>Save a ROOT-based analyzer figure without opening a GUI.</td>
    </tr>
  </tbody>
</table>

## Tests

Run the standalone Python tests:

```shell
pytest
pytest tests/test_analyzer.py
pytest tests/test_cli.py
pytest tests/test_gconfiguration_yaml.py
pytest tests/test_geometry.py
pytest -v
pytest -k "sqlite"
```

The tests cover analyzer plotting, CLI behavior, YAML-driven PyVista configuration, and geometry database
generation. They intentionally do not require Geant4 or a compiled `gemc` executable; full simulation tests live
in the parent GEMC Meson build.

## Project Layout

| Path                   | Purpose                                                                   |
| ---------------------- | ------------------------------------------------------------------------- |
| `src/pygemc/api/`      | Geometry, materials, units, SQLite output, PyVista support, and templates |
| `src/pygemc/analyzer/` | CSV/ROOT readers, plotting, and analyzer CLI                              |
| `tests/`               | Standalone pytest suite                                                   |
| `releases/`            | Release notes                                                             |
| `pyproject.toml`       | Python packaging metadata and console scripts                             |
| `meson.build`          | Meson subproject integration used by GEMC                                 |

## Documentation

- [GEMC homepage](https://gemc.github.io/home/)
- [Python API overview](https://gemc.github.io/home/documentation/api/pyvista_api.html)
- [Quickstart](https://gemc.github.io/home/documentation/quickstart/)
- [Examples](https://gemc.github.io/home/examples/)
- [GEMC source repository](https://github.com/gemc/src)
- [CLAS12 GEMC systems repository](https://github.com/gemc/clas12-systems)
- [Documentation website repository](https://github.com/gemc/home)
- [GEMC2 / CLAS12 repository](https://github.com/gemc/clas12Tags)

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
