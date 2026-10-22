#!/usr/bin/env python3
"""Create a Python 3.10-3.14 environment, preserving environments from another Python version."""

from pathlib import Path
import subprocess
import sys
import tempfile
import venv


def prepare_env(directory):
    if not (3, 10) <= sys.version_info[:2] < (3, 15):
        raise SystemExit('pygemc requires Python 3.10-3.14; select a supported interpreter first.')

    directory = Path(directory)
    if directory.exists():
        try:
            version = subprocess.check_output(
                [str(directory / 'bin/python3'), '-c', 'import sys; print(sys.version_info[:2])'], text=True,
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            version = ''
        if version == str(sys.version_info[:2]):
            print(f' > Reusing Python environment at {directory}', flush=True)
            return False
        backup_root = Path(tempfile.mkdtemp(prefix=directory.name + '-backup-', dir=directory.parent))
        backup = backup_root / directory.name
        directory.rename(backup)
        print(f' > Preserved previous Python environment at {backup}', flush=True)

    print(f' > Creating Python environment at {directory}', flush=True)
    venv.create(directory, with_pip=True)
    return True


if __name__ == '__main__':
    prepare_env(sys.argv[1])
