"""El arranque debe mostrar la ventana, no solo construir los widgets."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]
STARTUP_CHECK = r"""
import sys
import traceback

sys.path.insert(0, sys.argv[1])
import geforia.app
import main

errors = []

class CheckedApp(geforia.app.App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.check_index = 0
        self.after(100, self.check_window)

    def report_callback_exception(self, *args):
        traceback.print_exception(*args)
        errors.append("Error en un callback de Tk")
        self.quit()

    def check_window(self):
        # El gestor de ventanas puede mapear los hijos después del primer timer.
        # El timeout del proceso detecta si nunca llegan a estar visibles.
        if not (self.winfo_viewable()
                and all(button.winfo_viewable() for button in self.nav.values())
                and self.pages[self.current_page].winfo_viewable()):
            self.after(25, self.check_window)
            return
        print("VISIBLE", self.current_page, self.geometry(), flush=True)
        pages = ("measurement", "history", "profile") * 2
        if self.check_index < len(pages):
            if self.check_index == 3:
                self.geometry("960x680")
            self.show(pages[self.check_index])
            self.check_index += 1
            self.after(100, self.check_window)
        else:
            self.close()
            assert self.closing
            print("CLOSED", flush=True)

geforia.app.App = CheckedApp
status = main.main(["--data-dir", sys.argv[2], *sys.argv[3:]])
raise SystemExit(status or bool(errors))
"""


class StartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import tkinter as tk
        except ImportError as exc:
            raise unittest.SkipTest(f'Tkinter no disponible: {exc}')
        try:
            root = tk.Tk()
            root.withdraw()
            root.destroy()
        except tk.TclError as exc:
            raise unittest.SkipTest(f'No hay pantalla gráfica accesible: {exc}')

    def test_cli_maps_window_and_keeps_event_loop_responsive(self):
        for demo in (False, True):
            with self.subTest(demo=demo), tempfile.TemporaryDirectory() as folder:
                command = [sys.executable, '-u', '-c', STARTUP_CHECK, str(PROJECT), folder]
                if demo:
                    command.append('--demo')
                try:
                    result = subprocess.run(command, cwd=folder, capture_output=True,
                                            text=True, timeout=10)
                except subprocess.TimeoutExpired as exc:
                    output = (exc.stdout or b'').decode(errors='replace')
                    raise AssertionError('El arranque se bloqueó durante 10 s sin '
                                         f'mostrar/cerrar la ventana.\n{output}') from None
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                for page in ('profile', 'measurement', 'history'):
                    self.assertIn(f'VISIBLE {page}', result.stdout)
                self.assertIn('CLOSED', result.stdout)
                data_dir = Path(folder) / 'demo' if demo else Path(folder)
                self.assertTrue((data_dir / 'registros.sqlite3').is_file())
                if demo:
                    self.assertFalse((Path(folder) / 'registros.sqlite3').exists())


if __name__ == '__main__':
    unittest.main()
