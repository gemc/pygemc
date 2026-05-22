# pygemc
Python API for GEMC geometry definition and output analysis.

---

## Setup

Create and activate a virtual environment, then install pygemc in editable mode
(editable means changes to the source are immediately reflected — no reinstall needed):

```shell
python3 -m venv ~/venv/pygemc          # create (once)
source ~/venv/pygemc/bin/activate      # activate (every new terminal)
pip install -e /path/to/pygemc         # install pygemc + all dependencies
```

---

## Running the tests

```shell
pytest                         # run all tests
pytest tests/test_cli.py       # only CLI tests (fast, ~2s)
pytest tests/test_geometry.py  # only geometry-building tests (~65s)
pytest -v                      # verbose: print each test name as it runs
pytest -k "G4Box"              # only tests whose name contains "G4Box"
pytest -k "sqlite"             # only sqlite-format tests
```

The tests only require Python and pygemc — no Geant4 or gemc binary needed.

---

## How the tests work

### pytest basics

pytest discovers test files automatically (any file named `test_*.py`) and runs
any function whose name starts with `test_`. A test passes if it returns without
raising an exception, and fails if it raises one (including `AssertionError` from
a failed `assert` statement).

### `@pytest.mark.parametrize` — running one test with many inputs

Instead of writing a separate test function for every Geant4 solid type, we write
one function and tell pytest to call it once per solid:

```python
@pytest.mark.parametrize("solid", ["G4Box", "G4Tubs", "G4Cons"])
def test_show_template_code(solid):
    run_cli("-gv", solid)
```

pytest expands this into three independent tests:
- `test_show_template_code[G4Box]`
- `test_show_template_code[G4Tubs]`
- `test_show_template_code[G4Cons]`

You can also parametrize over pairs of values:

```python
@pytest.mark.parametrize("solid,pars", SOLIDS.items())
def test_show_template_code_with_parameters(solid, pars):
    ...
```

This is equivalent to one test per key-value pair in the `SOLIDS` dictionary.

Stacking two `@pytest.mark.parametrize` decorators produces the Cartesian product —
every combination:

```python
@pytest.mark.parametrize("solid", SOLIDS)
@pytest.mark.parametrize("fmt", ["ascii", "sqlite"])
def test_build_geometry_per_solid(tmp_path, solid, fmt):
    ...
```

This generates 6 solids × 2 formats = 12 tests.

### `tmp_path` — automatic temporary directories

`tmp_path` is a built-in pytest fixture: when you declare it as a function argument,
pytest automatically creates a fresh temporary directory for that test and passes it
in. The directory is deleted after the test finishes. This means tests never
interfere with each other and leave no files behind.

```python
def test_create_system(tmp_path):
    run_cli("-s", "test", cwd=tmp_path)   # files are created inside tmp_path
    assert (tmp_path / "test" / "test.py").exists()
```

### `conftest.py` — shared setup

`conftest.py` is a special pytest file that is loaded automatically before any tests
run. It is used to define:

- **Shared helpers** (`run_cli`, `run_python`) so every test file can call them
  without repeating the `subprocess.run` boilerplate.
- **Shared data** (`SOLIDS` dictionary) that both `test_cli.py` and `test_geometry.py`
  use, keeping the solid list in one place.
- **Session fixtures** (`require_cli`) that run once for the whole test session —
  here it checks that `gemc-system-template` is installed and skips all tests with
  a clear message if it is not, rather than failing with a confusing error.

### `@pytest.fixture` — reusable setup code

A function decorated with `@pytest.fixture` is called by pytest automatically when
a test declares it as an argument. `tmp_path` above is a built-in example. The
`require_cli` fixture in `conftest.py` uses `scope="session"` and `autouse=True`,
which means: run it once per session, for every test, without tests having to
declare it explicitly.

---

## Test structure

```
tests/
  conftest.py        shared helpers, SOLIDS data, CLI availability check
  test_cli.py        gemc-system-template CLI: help, solid listing, code display
  test_geometry.py   geometry building: create system, build sqlite/ascii databases
```

### What is tested

| Test file | What it checks |
|---|---|
| `test_cli.py` | CLI exits 0 for help, solid listing, and code display for all solid types |
| `test_geometry.py` | System template creates expected files; geometry Python scripts produce databases |

The geometry tests mirror the priority-ordered sequence used in the src meson build:
1. Create a system with `gemc-system-template -s <name>`
2. Run the generated `<name>.py -f <format>` to build the geometry database
3. Verify the output file exists

The gemc binary tests (running `gemc <name>.yaml`) are not included here — those
require the compiled C++ binary and live in the src meson build.
