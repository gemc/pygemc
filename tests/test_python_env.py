"""Offline checks for the shared Python environment setup and Meson installer."""

from contextlib import redirect_stdout
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

CI = Path(__file__).resolve().parents[1] / 'ci'
sys.path.insert(0, str(CI))
import install_python_env as installer
import prepare_python_env as environments


class EnvironmentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name) / 'python_env'
        self.output = redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def test_supported_version_boundaries(self):
        for version in ((3, 10), (3, 14)):
            with self.subTest(version=version), patch.object(sys, 'version_info', version), \
                 patch.object(environments.venv, 'create') as create:
                self.assertTrue(environments.prepare_env(self.directory))
                create.assert_called_once_with(self.directory, with_pip=True)
        for version in ((3, 9), (3, 15)):
            with self.subTest(version=version), patch.object(sys, 'version_info', version), \
                 patch.object(environments.venv, 'create') as create:
                with self.assertRaisesRegex(SystemExit, '3.10-3.14'):
                    environments.prepare_env(self.directory)
                create.assert_not_called()

    def test_matching_environment_is_reused(self):
        self.directory.mkdir()
        with patch.object(environments.subprocess, 'check_output', return_value=str(sys.version_info[:2])), \
             patch.object(environments.venv, 'create') as create:
            self.assertFalse(environments.prepare_env(self.directory))
            create.assert_not_called()
        self.assertEqual(list(self.directory.parent.glob('python_env-backup-*')), [])

    def test_mismatched_and_broken_environments_are_preserved_on_creation_failure(self):
        for response in ('(3, 15)', FileNotFoundError()):
            with self.subTest(response=response):
                self.directory.mkdir()
                (self.directory / 'marker').write_text('preserved')
                options = ({'side_effect': response} if isinstance(response, Exception)
                           else {'return_value': response})
                with patch.object(environments.subprocess, 'check_output', **options), \
                     patch.object(environments.venv, 'create', side_effect=RuntimeError('creation failed')):
                    with self.assertRaisesRegex(RuntimeError, 'creation failed'):
                        environments.prepare_env(self.directory)
                self.assertFalse(self.directory.exists())
        backups = list(self.directory.parent.glob('python_env-backup-*/python_env/marker'))
        self.assertEqual([path.read_text() for path in backups], ['preserved', 'preserved'])


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.output = redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def test_skip_needs_no_install_prefix(self):
        with patch.dict(os.environ, {'GEMC_SKIP_PYTHON_ENV_INSTALL': '1'}, clear=True), \
             patch.object(installer, 'prepare_env') as prepare, \
             patch.object(installer.subprocess, 'run') as run:
            self.assertEqual(installer.main(), 0)
            prepare.assert_not_called()
            run.assert_not_called()

    def test_normal_and_staged_prefixes_install_from_the_owning_repository(self):
        for staged in (False, True):
            environment = {'MESON_INSTALL_PREFIX': '/install'}
            if staged:
                environment['MESON_INSTALL_DESTDIR_PREFIX'] = '/stage/install'
            prefix = '/stage/install' if staged else '/install'
            with self.subTest(staged=staged), patch.dict(os.environ, environment, clear=True), \
                 patch.object(installer, 'prepare_env', return_value=True) as prepare, \
                 patch.object(installer.subprocess, 'run') as run:
                self.assertEqual(installer.main(), 0)
                prepare.assert_called_once_with(Path(prefix) / 'python_env')
                self.assertEqual(run.call_count, 2)
                upgrade, install = run.call_args_list
                self.assertEqual(upgrade.args[0][0], prefix + '/python_env/bin/python3')
                self.assertIn('--upgrade', upgrade.args[0])
                self.assertEqual(install.args[0], [prefix + '/python_env/bin/python3', '-m', 'pip',
                                                 'install', str(CI.parent)])
                self.assertTrue(install.kwargs['check'])

    def test_reuse_only_updates_pygemc(self):
        with patch.dict(os.environ, {'MESON_INSTALL_PREFIX': '/install'}, clear=True), \
             patch.object(installer, 'prepare_env', return_value=False), \
             patch.object(installer.subprocess, 'run') as run:
            self.assertEqual(installer.main(), 0)
            self.assertEqual(run.call_count, 1)
            self.assertNotIn('--upgrade', run.call_args.args[0])

    def test_pip_failure_is_propagated(self):
        with patch.dict(os.environ, {'MESON_INSTALL_PREFIX': '/install'}, clear=True), \
             patch.object(installer, 'prepare_env', return_value=False), \
             patch.object(installer.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'pip')):
            with self.assertRaises(subprocess.CalledProcessError):
                installer.main()


if __name__ == '__main__':
    unittest.main()
