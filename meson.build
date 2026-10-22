project('pygemc', version: '0.4.0')

# Export the resolved source directory for consumers sharing this subproject.
pygemc_source_dir = meson.current_source_dir()

# Keep the active Python when supported, otherwise find an installed Python 3.10-3.14.
python_module = import('python')
python3 = python_module.find_installation('python3')
if not (python3.language_version().version_compare('>=3.10') and
        python3.language_version().version_compare('<3.15'))
  supported_python = find_program('python3.14', 'python3.13', 'python3.12', 'python3.11', 'python3.10',
                                  required: false)
  if not supported_python.found()
    error('pygemc requires Python 3.10-3.14. Install a supported Python and add it to PATH.')
  endif
  python3 = python_module.find_installation(supported_python.full_path())
endif

# Place the venv in the build tree so meson setup works even when the install
# prefix does not exist yet (e.g. after 'rm -rf $GEMC' in ci/build.sh, or on
# read-only install prefixes such as CVMFS). This subproject also registers
# the install hook that creates the separate environment at the install prefix.
venv_dir = meson.current_build_dir() / 'python_env'

message('Creating Python virtual environment at: ' + venv_dir)
run_command(python3, files('ci/prepare_python_env.py'), venv_dir, check: true)

message('Installing pygemc into the virtual environment...')
# Pre-install the build backend so pip can use --no-build-isolation below,
# avoiding a second PyPI fetch inside the isolated build environment.
run_command(venv_dir / 'bin' / 'python3', '-m', 'pip', 'install',
            'hatchling', 'hatch-vcs', check: false)

# --no-deps: avoids downloading vtk/pyvista/pyqt6 (~200 MB) at configure time;
# those are installed into the prefix venv by this subproject's install hook.
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

# Export the build interpreter and register installation once for all consuming projects.
python_exe = python_module.find_installation(venv_bin / 'python3')
meson.add_install_script(python3, files('ci/install_python_env.py'))
