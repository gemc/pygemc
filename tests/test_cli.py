# test_cli.py — tests for the gemc-system-template command-line interface.
#
# These tests only invoke the CLI and check that it exits successfully (exit
# code 0).  They do not create geometry databases and finish in a few seconds.
# They mirror the 'api_template_help', 'api_show_solid_creators', and
# 'api_show_template_code_for_*' tests in the src meson build.

import pytest
from conftest import SOLIDS, run_cli


def test_help():
    # -h prints usage and exits 0; check=True in run_cli would raise if non-zero.
    run_cli("-h")


def test_show_solid_creators():
    # -sl lists all supported Geant4 solid types.
    run_cli("-sl")


# @pytest.mark.parametrize repeats the test once for each value in the list.
# pytest names each run with the parameter value, e.g. test_show_template_code[G4Box].
@pytest.mark.parametrize("solid", SOLIDS)
def test_show_template_code(solid):
    # -gv prints example Python code for creating a volume of the given solid type.
    run_cli("-gv", solid)


# SOLIDS.items() yields (solid, parameters) pairs, so the test receives both.
@pytest.mark.parametrize("solid,pars", SOLIDS.items())
def test_show_template_code_with_parameters(solid, pars):
    # -gvp provides concrete parameter values; spaces are removed to match the
    # format the CLI expects (e.g. "10*cm 10*cm" → "10*cm10*cm" — single token).
    run_cli("-gv", solid, "-gvp", pars.replace(" ", ""))


def test_show_template_code_silent():
    # -silent suppresses decorative output; result should still exit 0.
    run_cli("-gv", "G4Cons", "-silent")
