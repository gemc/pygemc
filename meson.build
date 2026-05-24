project('pygemc', version: '0.1.0')

# Use whatever python3 is on PATH to bootstrap the venv.
# The venv (and everything in it) is what the parent project uses for all tests.
python3 = find_program('python3')

# Place the venv in the build tree so meson setup works even when the install
# prefix does not exist yet (e.g. after 'rm -rf $GEMC' in ci/build.sh, or on
# read-only install prefixes such as CVMFS).  A separate install-time venv is
# created at the prefix by ci/install_python_env.py via meson.add_install_script.
venv_dir = meson.current_build_dir() / 'python_env'

message('Creating Python virtual environment at: ' + venv_dir)
run_command(python3, '-m', 'venv', venv_dir, check: true)

message('Installing pygemc into the virtual environment...')
# Pre-install the build backend so pip can use --no-build-isolation below,
# avoiding a second PyPI fetch inside the isolated build environment.
run_command(venv_dir / 'bin' / 'python3', '-m', 'pip', 'install',
            'hatchling', 'hatch-vcs', check: false)

# --no-deps: avoids downloading vtk/pyvista/pyqt6 (~200 MB) at configure time;
# those are installed into the prefix venv at install time by ci/install_python_env.py.
# --no-build-isolation: uses the hatchling we just installed instead of letting
# pip create yet another isolated venv that would need a fresh PyPI download.
_r = run_command(venv_dir / 'bin' / 'python3', '-m', 'pip', 'install',
                 '--no-deps', '--no-build-isolation',
                 meson.current_source_dir(), check: false)
if _r.returncode() != 0
  error('pip install pygemc failed:\n' + _r.stdout() + _r.stderr())
endif
run_command(venv_dir / 'bin' / 'python3', '-m', 'pip', 'install',
            'numpy', 'pandas', 'matplotlib', 'pyyaml', check: false)

# Expose the venv bin/ directory so the parent project can point python_exe
# and PATH at the venv, making 'import pygemc' and gemc-system-template
# available in all tests without any manual venv activation.
venv_bin = venv_dir / 'bin'
