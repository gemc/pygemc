# conftest.py — pytest loads this file automatically before any tests run.
# Anything defined here is available to all test files in this directory.

import shutil
import subprocess
import sys
import pytest


# The CLI command installed by pygemc (defined as a script in pyproject.toml).
CLI = "gemc-system-template"

# The Geant4 solid types tested, paired with valid parameter strings.
# This dictionary is defined once here and imported by both test files so that
# adding a new solid only requires a change in one place.
SOLIDS = {
    "G4Box":     "10 10 10 cm",
    "G4Tubs":    "0,20,40,0,360 cm deg",
    "G4Cons":    "10 20 30 40 10 0 360 cm deg",
    "G4Trd":     "30 10 40 15 60 cm",
    "G4TrapRAW": "10 20 30 40",
    "G4TrapG":   "60 20 5 40 30 40 10 16 10 14 10 cm deg",
}


def run_cli(*args, cwd=None, check=True):
    """Run gemc-system-template with the given arguments.

    - cwd: working directory for the subprocess (important: template files are
           written relative to cwd, so tests pass a shared directory here).
    - check=True: raises subprocess.CalledProcessError if the command exits
                  with a non-zero status, which pytest catches as a test failure.
    """
    return subprocess.run(
        [CLI, *args],
        capture_output=True, text=True,
        cwd=cwd, check=check,
    )


def run_python(script, *args, cwd=None, check=True):
    """Run a Python script using the same interpreter that is running pytest.

    Using sys.executable ensures we use the active venv's Python, not whatever
    'python3' resolves to on the system PATH.
    """
    return subprocess.run(
        [sys.executable, script, *args],
        capture_output=True, text=True,
        cwd=cwd, check=check,
    )


# scope="session" means this fixture runs once for the entire test session, not
# once per test.  autouse=True means every test uses it automatically without
# having to declare it as an argument.
@pytest.fixture(scope="session", autouse=True)
def require_cli():
    """Skip all tests with a clear message if gemc-system-template is not installed."""
    if shutil.which(CLI) is None:
        pytest.skip(f"{CLI} not found — run: pip install -e /path/to/pygemc")


@pytest.fixture(scope="session")
def basic_system_dir(tmp_path_factory):
    """Create the 'test' template system once for the whole session.

    tmp_path_factory is the session-scoped equivalent of tmp_path.
    All tests that need the basic 'test' system share this single directory,
    avoiding redundant system-creation subprocess calls.
    """
    base = tmp_path_factory.mktemp("basic")
    run_cli("-s", "test", cwd=base)
    return base


@pytest.fixture(scope="session")
def per_solid_dirs(tmp_path_factory):
    """Create one template system per solid, once for the whole session.

    Returns a dict mapping solid name → Path of its system directory.
    Shared across all parametrized format tests so each solid's system is
    created exactly once — mirroring the meson priority ordering where
    system creation runs before the format build tests.
    """
    base = tmp_path_factory.mktemp("solids")
    for solid in SOLIDS:
        run_cli("-s", f"test_{solid}", cwd=base)
    return base
