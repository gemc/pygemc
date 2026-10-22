#!/usr/bin/env python3
"""Install pygemc and its dependencies into the Python environment at the Meson install prefix."""

import os
from pathlib import Path
import subprocess
import sys

from prepare_python_env import prepare_env


def main():
    if os.environ.get('GEMC_SKIP_PYTHON_ENV_INSTALL') == '1':
        print(' > Skipping Python environment installation (GEMC_SKIP_PYTHON_ENV_INSTALL=1)')
        return 0

    prefix = Path(os.environ.get('MESON_INSTALL_DESTDIR_PREFIX') or os.environ['MESON_INSTALL_PREFIX'])
    source = Path(__file__).resolve().parents[1]
    directory = prefix / 'python_env'
    python = str(directory / 'bin/python3')

    if prepare_env(directory):
        subprocess.run([python, '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel'], check=True)
    subprocess.run([python, '-m', 'pip', 'install', str(source)], check=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
