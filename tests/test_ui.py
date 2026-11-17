"""Pruebas de widgets reales. Se omiten explícitamente si no hay pantalla."""
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch
from geforia.app import App
from geforia.ui.history import ConsultationDialog


class UserFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            root = tk.Tk()
            root.withdraw()
            root.destroy()
        except tk.TclError as exc:
            raise unittest.SkipTest(f'No hay pantalla gráfica accesible: {exc}')

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.app = App(Path(self.directory.name), demo=True)
        self.app.report_callback_exception = lambda *args: self.fail(str(args))
        self.app.update()

    def tearDown(self):
        self.app.closing = True
        if self.app.after_id is not None:
            self.app.after_cancel(self.app.after_id)
        self.app.connection.disconnect()
        if self.app.connection.worker:
            self.app.connection.worker.join(timeout=2)
        self.app.database.cerrar()
        self.app.destroy()
        self.directory.cleanup()

    def fill_basics(self):
        page = self.app.profile_page
        page.vars['nombre'].set('Persona de prueba')
        page.vars['edad'].set('30')

    def test_window_builds_all_pages(self):
        self.assertEqual(set(self.app.pages), {'profile', 'measurement', 'history'})
        self.assertEqual(self.app.current_page, 'profile')

    def test_draft_survives_navigation(self):
        self.fill_basics()
        self.app.show('history')
        self.app.show('profile')
        self.assertEqual(self.app.profile_page.vars['nombre'].get(), 'Persona de prueba')
        self.assertTrue(self.app.profile_page.dirty)

    def test_invalid_field_prevents_advancing(self):
        page = self.app.profile_page
        page.vars['edad'].set('abc')
        self.assertFalse(page.go_step(1))
        self.assertEqual(page.step, 0)
        self.assertTrue(page.fields['edad'].error.cget('text'))

    def test_optional_fields_and_review_keep_values(self):
        self.fill_basics()
        page = self.app.profile_page
        self.assertTrue(page.go_step(1))
        page.vars['peso'].set('72,5')
        self.assertTrue(page.go_step(2))
        page.go_step(1)
        self.assertEqual(page.vars['peso'].get(), '72,5')

    def test_minimum_save_locks_code_and_clears_dirty(self):
        self.fill_basics()
        page = self.app.profile_page
        self.assertTrue(page.save())
        self.app.update()
        self.assertIn('readonly', page.fields['id'].input.state())
        self.assertFalse(page.dirty)
        self.assertEqual(self.app.records.profile()['nombre'], 'Persona de prueba')

    def test_cancel_update_keeps_both_draft_and_original(self):
        self.fill_basics()
        page = self.app.profile_page
        page.save()
        page.vars['nombre'].set('Edición pendiente')
        with patch('tkinter.messagebox.askokcancel',return_value=False):
            self.assertFalse(page.save())
        self.assertTrue(page.dirty)
        self.assertEqual(self.app.records.profile()['nombre'], 'Persona de prueba')
        self.assertEqual(page.vars['nombre'].get(), 'Edición pendiente')

    def test_consultation_save_appears_in_history(self):
        self.fill_basics()
        self.app.profile_page.save()
        dialog = ConsultationDialog(self.app.history_page, self.app)
        self.app.update()
        dialog.vars['motivo'].set('Seguimiento de prueba')
        self.assertTrue(dialog.save())
        self.assertEqual(len(self.app.history_page.consultations.get_children()), 1)
        # Abrir y cerrar el diálogo no deja callbacks de scroll destruidos.
        self.app.show('profile')
        self.app.update()

    def test_completed_study_saves_and_opens_signal(self):
        self.fill_basics()
        self.app.profile_page.save()
        session = self.app.session
        session.handle('connected', 'DEMO')
        session.origin = 'DEMO'
        session.start()
        for index in range(40):
            session.handle('muestra', (index / 200, index / 40, 0.1))
        session.handle('resultado', (72.0, True, -0.4, -0.2))
        self.assertTrue(self.app.measurement_page.save())
        history = self.app.history_page
        self.app.show('history')
        self.app.update()
        keys = history.studies.get_children()
        self.assertEqual(len(keys), 1)
        history.studies.selection_set(keys[0])
        history.show_study()
        self.app.update()
        for child in self.app.winfo_children():
            if isinstance(child,tk.Toplevel):
                child.destroy()


if __name__=='__main__':
    unittest.main()
