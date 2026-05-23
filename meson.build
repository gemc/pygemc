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
# Non-editable + --no-deps: works with any pip version and avoids downloading
# vtk/pyvista/pyqt6 (~200 MB) at configure time.  Those heavy packages are
# installed into the prefix venv at install time by ci/install_python_env.py.
run_command(venv_dir / 'bin' / 'python3', '-m', 'pip', 'install', '--no-deps',
            meson.current_source_dir(), check: true)
run_command(venv_dir / 'bin' / 'python3', '-m', 'pip', 'install',
            'numpy', 'pandas', 'matplotlib', 'pyyaml', check: false)

# Expose the venv bin/ directory so the parent project can point python_exe
# and PATH at the venv, making 'import pygemc' and gemc-system-template
# available in all tests without any manual venv activation.
venv_bin = venv_dir / 'bin'
