"""Ejecución real de cmd.exe: se omite, no se simula, fuera de Windows."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(sys.platform == 'win32', 'Requiere cmd.exe y Python de Windows')
class WindowsBatchTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='GeFORIA BAT ')
        self.addCleanup(directory.cleanup)
        self.folder = Path(directory.name)
        self.project = self.folder / 'proyecto con espacios (y !)'
        self.project.mkdir()
        for name in ('iniciar_geforia.bat', 'iniciar_demo.bat', 'requirements.txt'):
            shutil.copy2(PROJECT / name, self.project / name)
        (self.project / 'geforia').mkdir()
        shutil.copy2(PROJECT / 'geforia' / 'windows_launcher.py',
                     self.project / 'geforia' / 'windows_launcher.py')
        (self.project / 'main.py').write_text(
            'import json, sys\nprint("APP_JSON=" + json.dumps([sys.executable, sys.argv[1:]]))\n',
            encoding='utf-8')
        self.ready = self.project / '.venv-windows' / '.geforia-ready.json'

    def launch(self, name='iniciar_geforia.bat', arguments='', env=None):
        cmd = os.environ.get('COMSPEC', r'C:\Windows\System32\cmd.exe')
        command = f'"{cmd}" /d /s /c ""{self.project / name}" {arguments}"'
        return subprocess.run(command, cwd=self.folder, env=env, input='\n',
                              capture_output=True, text=True, timeout=120)

    def application_result(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        line = next(line for line in result.stdout.splitlines() if line.startswith('APP_JSON='))
        return json.loads(line.split('=', 1)[1])

    def test_first_setup_reuse_and_demo_forward_arguments_from_other_directory(self):
        result = self.launch(arguments='--help')
        executable, args = self.application_result(result)
        self.assertEqual(Path(executable), self.project / '.venv-windows' / 'Scripts' / 'python.exe')
        self.assertEqual(args, ['--help'])
        self.assertTrue(self.ready.is_file())
        stamp = self.ready.stat().st_mtime_ns
        data = self.folder / 'datos de prueba'
        result = self.launch('iniciar_demo.bat', f'--data-dir "{data}"')
        executable, args = self.application_result(result)
        self.assertEqual(args, ['--demo', '--data-dir', str(data)])
        self.assertNotIn('Preparando GeFORIA', result.stdout)
        self.assertEqual(self.ready.stat().st_mtime_ns, stamp)
        self.assertFalse(data.exists())  # El main de esta prueba solo registra argumentos.

    def test_interrupted_setup_can_retry_after_installation_error(self):
        (self.project / 'requirements.txt').write_text('esto no es un requisito ???\n')
        result = self.launch(arguments='--help')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.ready.exists())
        self.assertIn('GUIA_WINDOWS.md', result.stdout)
        self.assertIn('Pulsa una tecla', result.stdout)
        shutil.copy2(PROJECT / 'requirements.txt', self.project / 'requirements.txt')
        self.application_result(self.launch(arguments='--help'))
        self.assertTrue(self.ready.is_file())

    def test_missing_python_keeps_readable_guidance(self):
        env = os.environ.copy()
        env['PATH'] = str(self.folder / 'sin python')
        result = self.launch(env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Python 3.10', result.stdout)
        self.assertIn('https://www.python.org/downloads/windows/', result.stdout)
        self.assertIn('GUIA_WINDOWS.md', result.stdout)
        self.assertFalse(self.ready.exists())

    def test_incomplete_download_keeps_readable_guidance(self):
        (self.project / 'main.py').unlink()
        result = self.launch()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Extrae TODO el ZIP', result.stdout)
        self.assertIn('Pulsa una tecla', result.stdout)


if __name__ == '__main__':
    unittest.main()
