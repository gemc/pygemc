project('pygemc', version: '0.1.0')

# Use whatever python3 is on PATH to bootstrap the venv.
# The venv (and everything in it) is what the parent project uses for all tests.
python3 = find_program('python3')

venv_dir = get_option('prefix') / 'python_env'

message('Creating Python virtual environment at: ' + venv_dir)
run_command(python3, '-m', 'venv', venv_dir, check: true)

message('Installing pygemc into the virtual environment...')
run_command(venv_dir / 'bin' / 'python3', '-m', 'pip', 'install', '-e',
            meson.current_source_dir(), check: true)

# Expose the venv bin/ directory so the parent project can point python_exe
# and PATH at the venv, making 'import pygemc' and gemc-system-template
# available in all tests without any manual venv activation.
venv_bin = venv_dir / 'bin'
