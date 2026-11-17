"""Composición de servicios y ventanas; punto de coordinación de Tkinter."""
import logging
from pathlib import Path
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from .config import POLL_MS
from .persistence.database import Database
from .services.records import RecordService
from .services.acquisition import AcquisitionSession
from .services.connection_manager import ConnectionManager
from .ui import theme
from .ui.widgets import button, label
from .ui.profile import ProfilePage
from .ui.measurement import MeasurementPage
from .ui.history import HistoryPage

logger = logging.getLogger(__name__)


class App(tk.Tk):
    def __init__(self, data_dir: Path, demo=False):
        super().__init__()
        self.withdraw()
        self.demo = demo
        self.database = None
        try:
            self.database = Database(data_dir / 'registros.sqlite3')
            self.records = RecordService(self.database)
            self.session = AcquisitionSession()
            self.connection = ConnectionManager(demo=demo)
            self.closing = False
            self.after_id = None
            self.current_page = None
            theme.configure_theme(self)
            self.title('GeFORIA · Seguimiento personal' + (' · DEMO' if demo else ''))
            width = min(1240, max(760, self.winfo_screenwidth() - 60))
            height = min(850, max(600, self.winfo_screenheight() - 100))
            self.geometry(f'{width}x{height}')
            self.minsize(min(960, width), min(680, height))
            self._build_shell()
            self.protocol('WM_DELETE_WINDOW', self.close)
            self.bind('<Control-s>', self._save_shortcut)
            for number,key in enumerate(("profile","measurement","history"),1):
                self.bind(f'<Alt-Key-{number}>', lambda event, k=key: self.show(k))
            self.show('measurement' if self.records.active_id else 'profile')
            self.after_id = self.after(POLL_MS, self._poll)
            self.deiconify()
        except Exception:
            if self.database is not None:
                self.database.cerrar()
            self.destroy()
            raise

    def _build_shell(self):
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        sidebar = tk.Frame(self, bg=theme.NAVY, width=205, padx=17, pady=25)
        sidebar.grid(row=0, column=0, sticky='nsew')
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text='GeFORIA', font=(theme.FONT, 23, 'bold'), bg=theme.NAVY, fg='white', anchor='w').pack(fill='x')
        tk.Label(sidebar, text='SEGUIMIENTO PERSONAL', font=(theme.FONT, 8, 'bold'), bg=theme.NAVY, fg='#B8D9DE', anchor='w').pack(fill='x', pady=(4, 32))
        self.nav = {}
        for title,key in (("01   Mis datos","profile"),("02   Medición","measurement"),("03   Historial","history")):
            btn=tk.Button(sidebar,text=title,command=lambda k=key:self.show(k),anchor="w",padx=12,pady=14,
                relief="flat",borderwidth=0,background=theme.NAVY,foreground="#DDECF0",activebackground="#214754",
                activeforeground="white",font=(theme.FONT,10,"bold"),cursor="hand2",highlightthickness=2,
                highlightbackground=theme.NAVY,highlightcolor="#7AE0D1",takefocus=True)
            btn.pack(fill='x', pady=(0, 6))
            self.nav[key] = btn
        bottom = tk.Frame(sidebar, bg=theme.NAVY)
        bottom.pack(side='bottom', fill='x')
        self.sidebar_person = tk.Label(bottom, text='', wraplength=160, justify='left', anchor='w', bg=theme.NAVY, fg='#DDECF0', font=(theme.FONT, 10))
        self.sidebar_person.pack(fill='x', pady=(0, 14))
        tk.Label(bottom, text='MODO DEMOSTRACIÓN\nDatos simulados' if self.demo else 'PROTOTIPO ACADÉMICO\nUso exploratorio', font=(theme.FONT, 8, 'bold'), justify='left', anchor='w', bg=theme.NAVY, fg='#ADDAD3').pack(fill='x', pady=(0, 14))
        button(bottom, 'Crear respaldo', self.backup).pack(fill='x', pady=(0, 8))
        button(bottom, 'Ayuda', self.help).pack(fill='x')
        self.area = ttk.Frame(self, padding=(24, 22))
        self.area.grid(row=0, column=1, sticky='nsew')
        self.profile_page = ProfilePage(self.area, self)
        self.measurement_page = MeasurementPage(self.area, self)
        self.history_page = HistoryPage(self.area, self)
        self.pages = {'profile': self.profile_page, 'measurement': self.measurement_page, 'history': self.history_page}
        self.profile_saved()

    def show(self,key):
        if key not in self.pages:
            return
        for name,page in self.pages.items():
            page.pack_forget()
            self.nav[name].configure(bg="#24515C" if name==key else theme.NAVY,
                                     highlightbackground="#24515C" if name==key else theme.NAVY)
        self.pages[key].pack(fill='both', expand=True)
        self.current_page = key
        if key=="history":
            self.history_page.refresh()
        if key=="measurement":
            self.measurement_page.update_state()

    def profile_saved(self):
        profile = self.records.profile()
        self.sidebar_person.configure(text=profile['nombre'] if profile else 'Completa tus datos\npara comenzar')
        if hasattr(self,"history_page"):
            self.history_page.refresh()
        if hasattr(self,"measurement_page"):
            self.measurement_page.update_state()

    def _save_shortcut(self,event):
        # Los diálogos gestionan su propio Ctrl+S sin guardar otra pantalla debajo.
        if event.widget.winfo_toplevel() is not self:
            return
        if self.current_page=="profile":
            self.profile_page.save()
        elif self.current_page=="measurement" and self.session.can_save:
            self.measurement_page.save()
        return 'break'

    def _poll(self):
        if self.closing:
            return
        try:
            for kind,payload in self.connection.drain():
                self.session.handle(kind, payload)
                if kind=="error":
                    self.connection.disconnect()
                    self.measurement_page.notice = str(payload)
            self.measurement_page.update_state()
        except (tk.TclError,ValueError,sqlite3.Error):
            logger.exception('No se pudo actualizar la vista de adquisición')
        finally:
            if not self.closing:
                self.after_id = self.after(POLL_MS, self._poll)

    def backup(self):
        target=filedialog.asksaveasfilename(parent=self,title="Guardar respaldo de GeFORIA",
            initialfile="GeFORIA_respaldo.sqlite3",defaultextension=".sqlite3",filetypes=[("Base SQLite","*.sqlite3")])
        if not target:
            return
        try:
            self.database.backup(target)
        except (sqlite3.Error,OSError,ValueError) as exc:
            messagebox.showerror('No se pudo crear el respaldo', str(exc), parent=self)
            return
        messagebox.showinfo('Respaldo creado', 'Se guardó una copia completa de tu expediente, mediciones y consultas.', parent=self)

    def help(self):
        messagebox.showinfo("Guía rápida · GeFORIA",
            "1. Mis datos: escribe nombre y edad. El código ya está listo. La salud es opcional.\n\n"
            "2. Medición: conecta el ESP32 por USB o Bluetooth SPP; selecciona el puerto, conecta e inicia la prueba. Espera el resultado y guarda.\n\n"
            "3. Historial: consulta las señales, registra consultas o elimina una medición seleccionada.\n\n"
            "Tab / Shift+Tab: recorrer campos. Ctrl+S: guardar. Alt+1 / Alt+2 / Alt+3: cambiar de sección.\n\n"
            "Una captura parcial debe detenerse con Desconectar antes de guardarse.\n"
            "Los índices proceden del ESP32 y no constituyen diagnósticos.",parent=self)

    def close(self):
        modal = self.grab_current()
        if modal is not None and modal is not self:
            modal.lift()
            modal.focus_set()
            return
        if self.profile_page.dirty:
            decision = messagebox.askyesnocancel('Cambios sin guardar', '¿Guardar los cambios de tu expediente antes de cerrar?', parent=self)
            if decision is None:
                return
            if decision and not self.profile_page.save():
                return
        if self.session.snapshot() is not None and not self.session.saved:
            if not messagebox.askokcancel("Medición sin guardar","La captura actual no está guardada. ¿Cerrar y descartarla?",parent=self,default="cancel"):
                return
        elif self.session.running:
            if not messagebox.askokcancel("Prueba en curso","¿Cerrar y desconectar la adquisición en curso?",parent=self,default="cancel"):
                return
        self.closing = True
        if self.after_id is not None:
            self.after_cancel(self.after_id)
        self.connection.disconnect()
        self.database.cerrar()
        self.destroy()
