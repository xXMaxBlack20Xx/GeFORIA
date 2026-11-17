"""La preparación Windows se comprueba sin instalar nada en el equipo de prueba."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from geforia import windows_launcher as launcher


class WindowsPreparationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='GeFORIA Windows ')
        self.addCleanup(directory.cleanup)
        self.project = Path(directory.name)
        self.requirements = self.project / 'requirements.txt'
        self.requirements.write_text('pyserial>=3.5,<4\n', encoding='utf-8')
        self.environment = self.project / launcher.ENVIRONMENT
        self.python = self.environment / 'Scripts' / 'python.exe'
        self.python.parent.mkdir(parents=True)
        self.python.touch()
        self.ready = self.environment / launcher.READY_FILE
        run_patch = patch.object(
            launcher.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0))
        self.run = run_patch.start()
        self.addCleanup(run_patch.stop)
        builder_patch = patch.object(launcher.venv, 'EnvBuilder')
        self.builder = builder_patch.start()
        self.addCleanup(builder_patch.stop)
        self.builder.return_value.create.side_effect = lambda _: self.python.touch()
        output = redirect_stdout(io.StringIO())
        output.__enter__()
        self.addCleanup(output.__exit__, None, None, None)

    def prepare(self):
        return launcher.prepare_environment(self.project)

    def install_commands(self):
        return [call.args[0] for call in self.run.call_args_list
                if 'install' in call.args[0]]

    def test_first_preparation_installs_then_reuses_environment(self):
        self.assertEqual(self.prepare(), self.python)
        self.assertEqual(len(self.install_commands()), 1)
        marker = self.ready.read_bytes()
        self.assertEqual(json.loads(marker), launcher.preparation_key(self.requirements))
        self.run.reset_mock()
        self.assertEqual(self.prepare(), self.python)
        self.assertFalse(self.install_commands())
        self.assertEqual(self.ready.read_bytes(), marker)
        self.builder.assert_not_called()

    def test_changed_requirements_trigger_new_preparation(self):
        self.prepare()
        self.requirements.write_text('pyserial>=3.5,<4\n# actualizado\n', encoding='utf-8')
        self.run.reset_mock()
        self.prepare()
        self.assertEqual(len(self.install_commands()), 1)
        self.assertEqual(json.loads(self.ready.read_text()), launcher.preparation_key(self.requirements))

    def test_corrupt_marker_can_be_retried(self):
        self.ready.write_text('{"incompleto":', encoding='utf-8')
        self.prepare()
        self.assertEqual(len(self.install_commands()), 1)
        self.assertEqual(json.loads(self.ready.read_text()), launcher.preparation_key(self.requirements))

    def test_incomplete_environment_is_repaired_without_clearing_files(self):
        self.python.unlink()
        sentinel = self.environment / 'conservar.txt'
        sentinel.write_text('No borrar', encoding='utf-8')
        self.prepare()
        self.builder.assert_called_once_with(with_pip=True)
        self.builder.return_value.create.assert_called_once_with(self.environment)
        self.assertEqual(sentinel.read_text(), 'No borrar')

    def test_missing_pip_uses_ensurepip(self):
        def run(command, **kwargs):
            code = 1 if command[-3:] == ['-m', 'pip', '--version'] else 0
            return subprocess.CompletedProcess(command, code)
        self.run.side_effect = run
        self.prepare()
        self.assertTrue(any('ensurepip' in call.args[0] for call in self.run.call_args_list))
        self.assertTrue(self.ready.is_file())

    def test_failed_install_is_not_marked_ready_and_next_attempt_succeeds(self):
        self.ready.write_text('obsoleto', encoding='utf-8')
        def run(command, **kwargs):
            if 'install' in command:
                raise subprocess.CalledProcessError(1, command)
            return subprocess.CompletedProcess(command, 0)
        self.run.side_effect = run
        with self.assertRaises(subprocess.CalledProcessError):
            self.prepare()
        self.assertFalse(self.ready.exists())
        self.run.side_effect = None
        self.prepare()
        self.assertTrue(self.ready.is_file())

    def test_missing_dependency_invalidates_a_previously_ready_environment(self):
        self.prepare()
        self.run.reset_mock()
        count = 0
        def run(command, **kwargs):
            nonlocal count
            if command[-1] == launcher.DEPENDENCY_CHECK:
                count += 1
                if count == 1:
                    return subprocess.CompletedProcess(command, 1)
            return subprocess.CompletedProcess(command, 0)
        self.run.side_effect = run
        self.prepare()
        self.assertEqual(len(self.install_commands()), 1)
        self.assertIn('--force-reinstall', self.install_commands()[0])

    def test_tk_failure_does_not_mark_preparation_ready(self):
        self.run.return_value = subprocess.CompletedProcess([], 1)
        with self.assertRaisesRegex(RuntimeError, 'Tkinter'):
            self.prepare()
        self.assertFalse(self.ready.exists())
        self.assertFalse(self.install_commands())

    def test_main_preserves_arguments_and_application_exit_code(self):
        args = ['--demo', '--data-dir', 'carpeta con espacios']
        self.run.return_value = subprocess.CompletedProcess([], 7)
        with patch.object(launcher, 'prepare_environment', return_value=self.python):
            self.assertEqual(launcher.main(args), 7)
        project = Path(launcher.__file__).resolve().parents[1]
        self.run.assert_called_once_with([str(self.python), str(project / 'main.py'), *args])

    def test_setup_failure_explains_retry_without_deleting_data(self):
        error = io.StringIO()
        with patch.object(launcher, 'prepare_environment', side_effect=OSError('sin permisos')):
            with redirect_stderr(error):
                self.assertEqual(launcher.main([]), 1)
        self.assertIn('sin permisos', error.getvalue())
        self.assertIn('No borres tus datos', error.getvalue())
        self.assertIn('GUIA_WINDOWS.md', error.getvalue())


if __name__ == '__main__':
    unittest.main()
