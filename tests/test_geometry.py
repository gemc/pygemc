# test_geometry.py — geometry building tests.
#
# Each test follows the same two-step sequence used in the src meson build:
#   1. Run gemc-system-template to create a Python geometry script (done once
#      per solid via session-scoped fixtures in conftest.py).
#   2. Run that script to build a geometry database (sqlite or ascii format).
# No gemc binary is needed — these are pure Python operations.
#
# Session-scoped fixtures (basic_system_dir, per_solid_dirs) mean the system
# creation subprocess runs once per session, not once per test — matching the
# meson behaviour where system creation has higher priority and runs first.

import pytest
from conftest import SOLIDS, run_cli, run_python
from pygemc.api.gvolume import GVolume


# ---------------------------------------------------------------------------
# Basic system: verify files exist, then build for each format
# ---------------------------------------------------------------------------

def test_add_rotation_emits_single_triple_for_one_rotation():
    volume = GVolume("rotated_box")

    volume.add_rotation(0, 0, 40)

    assert volume.get_rotation_string() == "0*deg, 0*deg, 40*deg"


def test_add_rotation_emits_double_rotation_for_two_rotations():
    volume = GVolume("rotated_box")

    volume.add_rotation(0, 0, 40)
    volume.add_rotation(10, 0, 0)

    assert volume.get_rotation_string() == (
        "doubleRotation: 0*deg, 0*deg, 40*deg, 10*deg, 0*deg, 0*deg"
    )


def test_add_rotation_after_set_rotation_emits_double_rotation():
    volume = GVolume("rotated_box")

    volume.set_rotation(0, 0, 40)
    volume.add_rotation(10, 0, 0)

    assert volume.get_rotation_string() == (
        "doubleRotation: 0*deg, 0*deg, 40*deg, 10*deg, 0*deg, 0*deg"
    )


def test_add_rotation_rejects_more_than_two_rotations():
    volume = GVolume("rotated_box")

    volume.add_rotation(0, 0, 40)
    volume.add_rotation(10, 0, 0)
    volume.add_rotation(0, 20, 0)

    with pytest.raises(SystemExit, match="supports at most two"):
        volume.get_rotation_string()


def test_create_system(basic_system_dir):
    # basic_system_dir already ran 'gemc-system-template -s test'; just assert.
    test_dir = basic_system_dir / "test"
    assert (test_dir / "test.py").exists()
    assert (test_dir / "test.yaml").exists()
    assert (test_dir / "geometry.py").exists()
    assert (test_dir / "materials.py").exists()


@pytest.mark.parametrize("fmt", ["ascii", "sqlite"])
def test_build_geometry(basic_system_dir, fmt):
    # System already created by the fixture; just run the build step.
    test_dir = basic_system_dir / "test"
    run_python("test.py", "-f", fmt, cwd=test_dir)
    if fmt == "sqlite":
        assert (test_dir / "gemc.db").exists()


# ---------------------------------------------------------------------------
# Per-solid: generate replacement geometry code, then build for each format
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("solid,pars", SOLIDS.items())
def test_write_replacement_geometry(per_solid_dirs, solid, pars):
    """Verify that -write_to generates a valid geometry code file.

    The generated file is a standalone Python module — it is not automatically
    wired into the system; that step is left to the developer.
    """
    test_name = f"test_{solid}"
    out_file = f"geometry_test_{solid}.py"

    # System already created by per_solid_dirs fixture; only run the code-gen step.
    run_cli(
        "-gv", solid,
        "-gvp", pars,
        f"-write_to={out_file}",        # write code to this file instead of stdout
        f"-geo_sub=build_{test_name}",  # name of the Python function to generate
        cwd=per_solid_dirs,
    )

    assert (per_solid_dirs / out_file).exists()
    content = (per_solid_dirs / out_file).read_text()
    assert f"def build_{test_name}" in content  # function was generated
    assert "GVolume" in content                 # uses pygemc correctly


# Stacking two @parametrize decorators creates the Cartesian product:
# 6 solids × 2 formats = 12 tests — all sharing the same pre-built per_solid_dirs.
@pytest.mark.parametrize("solid", SOLIDS)
@pytest.mark.parametrize("fmt", ["ascii", "sqlite"])
def test_build_geometry_per_solid(per_solid_dirs, solid, fmt):
    # System already created by the session fixture; just run the build step.
    test_name = f"test_{solid}"
    test_dir = per_solid_dirs / test_name
    run_python(f"{test_name}.py", "-f", fmt, cwd=test_dir)
    if fmt == "sqlite":
        assert (test_dir / "gemc.db").exists()
