"""El lanzador conserva rutas y argumentos, incluso con espacios."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


@unittest.skipIf(sys.platform == 'win32', 'El lanzador Bash es para Linux/macOS')
class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='GeFORIA lanzador ')
        self.addCleanup(self.directory.cleanup)
        self.folder = Path(self.directory.name)
        self.project = self.folder / 'proyecto con espacios'
        self.project.mkdir()
        source = Path(__file__).resolve().parents[1] / 'iniciar_geforia.sh'
        self.launcher = self.project / source.name
        shutil.copy2(source, self.launcher)

    def run_launcher(self, *args):
        return subprocess.run([str(self.launcher), *args], cwd=self.folder,
                              capture_output=True, text=True, timeout=5)

    def test_uses_project_python_and_forwards_arguments_from_another_directory(self):
        main = self.project / 'main.py'
        main.write_text('import json, sys\nprint(json.dumps([sys.executable, sys.argv[1:]]))\n')
        python = self.project / '.venv' / 'bin' / 'python'
        python.parent.mkdir(parents=True)
        python.symlink_to(sys.executable)
        args = ['--demo', '--data-dir', 'datos con espacios']
        result = self.run_launcher(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [str(python), args])

    def test_missing_environment_explains_how_to_prepare_it(self):
        (self.project / 'main.py').touch()
        result = self.run_launcher('--demo')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('python3 -m venv .venv', result.stderr)
        self.assertIn('pip install -r requirements.txt', result.stderr)

    def test_missing_project_reports_main_file(self):
        result = self.run_launcher()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('No se encuentra main.py', result.stderr)


if __name__ == '__main__':
    unittest.main()
