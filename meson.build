project('pygemc', version: '0.1.0')

py = import('python').find_installation('python3')

# Install pygemc into the active Python environment as an editable package.
# This runs during 'meson setup', so 'import pygemc' works in all subsequent
# tests and builds without any manual PYTHONPATH configuration.
message('Installing pygemc into the active Python environment...')
run_command(py, '-m', 'pip', 'install', '-e', meson.current_source_dir(),
            check: true)
