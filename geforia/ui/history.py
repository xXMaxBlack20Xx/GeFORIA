"""Consulta de estudios y seguimiento, sin mezclar tablas con formularios."""
import json
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import zlib
from ..validation import ValidationError
from .widgets import ScrollFrame, FormField, button, label, table, text_input
from .plot import SignalPlot
from . import theme


def format_number(value, precision=3):
    return f'{value:.{precision}f}' if value is not None else '—'


class ConsultationDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title('Nueva consulta · GeFORIA')
        self.configure(background=theme.BG)
        self.transient(app)
        self.resizable(True, True)
        self.geometry('650x650')
        self.minsize(480, 460)
        self.protocol('WM_DELETE_WINDOW', self.close)
        outer = ttk.Frame(self, padding=20)
        outer.pack(fill='both', expand=True)
        label(outer, 'Registrar una consulta', 'Title.TLabel').pack(anchor='w')
        label(outer, 'Se agregará a tu expediente con la fecha y hora actuales.', 'Muted.TLabel', wraplength=580).pack(anchor='w', pady=(5, 16))
        actions = ttk.Frame(outer)
        actions.pack(side='bottom', fill='x', pady=(14, 0))
        button(actions, 'Cancelar', self.close).pack(side='left')
        button(actions, 'Guardar consulta', self.save, primary=True).pack(side='right')
        scroll = ScrollFrame(outer)
        scroll.pack(fill='both', expand=True)
        card = scroll.content
        self.vars = {key: tk.StringVar() for key in ('motivo', 'presion', 'medicacion')}
        self.fields = {}
        for key,title,help_text in (("motivo","Motivo / tipo de consulta","Por ejemplo: seguimiento con especialista."),
                                    ("presion","Presión arterial","Si la conoces; ejemplo: 120/80 mmHg."),
                                    ("medicacion","Medicamentos / cambios","Opcional; puedes dejarlo vacío.")):
            field = FormField(card, title, self.vars[key], help_text=help_text)
            field.pack(fill='x', pady=(0, 4))
            self.fields[key] = field
        label(card, 'Notas e indicaciones', 'Card.TLabel').pack(anchor='w', pady=(2, 5))
        self.notes = text_input(card, height=3)
        self.notes.pack(fill='both', expand=True)
        self.bind('<Control-s>', lambda e: self.save())
        self.bind('<Escape>', lambda e: self.close())
        self.grab_set()
        self.fields['motivo'].input.focus_set()

    def values(self):
        return {**{k: v.get() for k, v in self.vars.items()}, 'notas': self.notes.get('1.0', 'end-1c')}

    def close(self):
        if any(v.strip() for v in self.values().values()):
            if not messagebox.askokcancel("Consulta sin guardar","¿Descartar lo escrito en esta consulta?",parent=self,default="cancel"):
                return
        self.destroy()

    def save(self):
        try:
            self.app.records.save_consultation(self.values())
        except ValidationError as exc:
            self.fields['motivo'].set_error(str(exc))
            self.fields['motivo'].input.focus_set()
            return False
        except (ValueError,sqlite3.Error) as exc:
            messagebox.showerror('No se pudo guardar', f'Lo escrito sigue en pantalla.\n\n{exc}', parent=self)
            return False
        self.app.history_page.refresh()
        self.app.history_page.notice.configure(text='Consulta guardada en tu historial.', foreground=theme.TEAL_DARK)
        self.destroy()
        return True


class HistoryPage(ttk.Frame):
    def __init__(self,parent,app):
        super().__init__(parent)
        self.app = app
        self.study_rows = {}
        self.consultation_rows = {}
        label(self, 'Tu historial, en un solo lugar', 'Title.TLabel').pack(anchor='w')
        self.person = label(self, '', 'Muted.TLabel')
        self.person.pack(anchor='w', pady=(5, 12))
        self.notice = label(self, 'Las mediciones y las consultas se guardan por separado.', 'Banner.TLabel', wraplength=820)
        self.notice.pack(fill='x', pady=(0, 12))
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)
        studies = ttk.Frame(self.notebook, padding=12)
        consultations = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(studies, text='Mediciones PPG / SDPTG')
        self.notebook.add(consultations, text='Consultas y seguimiento')
        toolbar = ttk.Frame(studies)
        toolbar.pack(fill='x', pady=(0, 12))
        label(toolbar, 'Buscar:', 'Muted.TLabel').pack(side='left', padx=(0, 8))
        self.search = tk.StringVar()
        ttk.Entry(toolbar, textvariable=self.search, width=22).pack(side='left', fill='x', expand=True, padx=(0, 10))
        button(toolbar, 'Actualizar', self.refresh).pack(side='left')
        self.count = label(studies, '', 'Muted.TLabel')
        self.count.pack(anchor='w', pady=(0, 7))
        columns=(("fecha","Fecha y hora",155),("bpm","BPM",75),("ba","b/a",75),("agi","AGI",75),
                 ("quality","Calidad",95),("origin","Conexión",95),("notes","Observaciones",230))
        frame, self.studies = table(studies, columns)
        frame.pack(fill='both', expand=True)
        actions = ttk.Frame(studies)
        actions.pack(fill='x', pady=(12, 0))
        self.detail_button = button(actions, 'Ver detalle y señal', self.show_study)
        self.detail_button.pack(side='left')
        self.delete_button = ttk.Button(actions, text='Eliminar selección', command=self.delete_study, style='Danger.TButton')
        self.delete_button.pack(side='right')
        self.studies.bind('<<TreeviewSelect>>', lambda e: self.update_actions())
        self.studies.bind('<Double-1>', lambda e: self.show_study())
        self.studies.bind('<Return>', lambda e: self.show_study())
        self.search.trace_add('write', lambda *_: self._filter_studies())
        toolbar = ttk.Frame(consultations)
        toolbar.pack(fill='x', pady=(0, 12))
        button(toolbar, 'Ver consulta completa', self.show_consultation).pack(side='left')
        self.new_consultation = button(toolbar, 'Nueva consulta', self.add_consultation, primary=True)
        self.new_consultation.pack(side='right')
        columns=(("fecha","Fecha y hora",155),("motivo","Motivo",200),("presion","Presión",115),
                 ("medicacion","Medicamentos",220),("notas","Notas",290))
        frame, self.consultations = table(consultations, columns)
        frame.pack(fill='both', expand=True)
        self.consultations.bind('<Double-1>', lambda e: self.show_consultation())
        self.consultations.bind('<Return>', lambda e: self.show_consultation())
        label(consultations, 'Selecciona una consulta y presiona Enter para leer todas sus notas.', 'Muted.TLabel').pack(anchor='w', pady=(8, 0))
        self.bind('<Configure>', lambda e: self.notice.configure(wraplength=max(250, e.width - 30)) if e.widget is self else None)
        self.update_actions()

    def refresh(self):
        profile = self.app.records.profile()
        self.person.configure(text=f"{profile['nombre']} · {profile['id']}" if profile else 'Primero configura tu expediente en Mis datos.')
        self.new_consultation.state(['!disabled'] if profile else ['disabled'])
        self.study_rows = {}
        self.consultation_rows = {}
        for item in self.consultations.get_children():
            self.consultations.delete(item)
        if profile:
            self.study_rows = {str(row['id']): row for row in self.app.database.studies(profile['id'])}
            self.consultation_rows = {str(row['id']): row for row in self.app.database.consultations(profile['id'])}
        for key,row in self.consultation_rows.items():
            self.consultations.insert('', 'end', iid=key, values=tuple((row[k] or '' for k in ('fecha', 'motivo', 'presion', 'medicacion', 'notas'))))
        self._filter_studies()

    def _filter_studies(self):
        selection = self.studies.selection()
        for item in self.studies.get_children():
            self.studies.delete(item)
        query = self.search.get().strip().casefold()
        count = 0
        for key,row in self.study_rows.items():
            if query and query not in " ".join(str(value or "") for value in row.values()).casefold():
                continue
            self.studies.insert("","end",iid=key,values=(row["fecha"],format_number(row["bpm"],1),
                format_number(row["indice_ba"]),format_number(row["agi"]),row["calidad"] or "Sin registrar",
                row["origen"],row["observaciones"] or ""))
            count += 1
        if selection and self.studies.exists(selection[0]):
            self.studies.selection_set(selection[0])
        self.count.configure(text=f'{count} medición(es) visibles · hasta 1000 recientes' if self.study_rows else 'Aún no hay mediciones. Conecta el ESP32 y guarda tu primera prueba.')
        self.update_actions()

    def update_actions(self):
        state = ['!disabled'] if self.studies.selection() else ['disabled']
        self.detail_button.state(state)
        self.delete_button.state(state)

    def delete_study(self):
        selection = self.studies.selection()
        if not selection:
            return
        row = self.study_rows.get(selection[0])
        if not row:
            return
        if not messagebox.askyesno("Eliminar medición",f"¿Eliminar la medición del {row['fecha']} y su señal?\nEl expediente y las demás mediciones se conservarán. No se puede deshacer.",parent=self,default="no"):
            return
        try:
            self.app.database.eliminar_estudio(row['id'])
        except sqlite3.Error as exc:
            messagebox.showerror('No se pudo eliminar', str(exc), parent=self)
            return
        self.refresh()
        self.notice.configure(text='Medición eliminada.', foreground=theme.TEAL_DARK)

    def _detail_window(self,title):
        window = tk.Toplevel(self)
        window.title(title + ' · GeFORIA')
        window.configure(background=theme.BG)
        window.geometry('850x680')
        window.minsize(550, 450)
        window.transient(self.app)
        outer = ttk.Frame(window, padding=20)
        outer.pack(fill='both', expand=True)
        button(outer, 'Cerrar', window.destroy).pack(side='bottom', anchor='e', pady=(10, 0))
        return (window, outer)

    def show_study(self):
        selection = self.studies.selection()
        if not selection:
            return
        row = self.study_rows.get(selection[0])
        if not row:
            return
        window, outer = self._detail_window('Detalle de medición')
        label(outer, row['fecha'], 'Title.TLabel').pack(anchor='w', pady=(0, 8))
        text=(f"BPM: {format_number(row['bpm'],1)}    b/a: {format_number(row['indice_ba'])}    AGI: {format_number(row['agi'])}\n"
              f"Conexión: {row['origen']}    Calidad: {row['calidad'] or 'Sin registrar'}\n"
              f"Estado: {row['estado']}\n{row['descripcion']}")
        label(outer, text, justify='left', wraplength=780).pack(anchor='w', pady=(0, 8))
        notes = text_input(outer, height=3)
        notes.insert('1.0', row['observaciones'] or 'Sin observaciones')
        notes.configure(state='disabled')
        notes.pack(fill='x', pady=(0, 8))
        try:
            data = self.app.database.signal_detail(row['id'])
            if data:
                times, values = (data['t'], data['y'])
                derivatives = data.get('sdptg') or [None] * len(times)
                plot = SignalPlot(outer)
                plot.pack(fill='both', expand=True)
                plot.set_data(times, values, derivatives)
                label(outer, 'Se muestran los últimos 8 s de la señal guardada.', 'Muted.TLabel').pack(anchor='w')
            else:
                label(outer, 'Esta medición anterior no contiene una señal almacenada.', 'Banner.TLabel').pack(fill='x', pady=15)
        except (sqlite3.Error,ValueError,KeyError,TypeError,zlib.error) as exc:
            label(outer, 'No se pudo leer la señal almacenada: ' + str(exc), 'Banner.TLabel', wraplength=760).pack(fill='x')

    def add_consultation(self):
        if self.app.records.active_id:
            ConsultationDialog(self, self.app)

    def show_consultation(self):
        selection = self.consultations.selection()
        if not selection:
            return
        row = self.consultation_rows.get(selection[0])
        if not row:
            return
        _, outer = self._detail_window('Detalle de consulta')
        label(outer, row['fecha'], 'Title.TLabel').pack(anchor='w', pady=(0, 12))
        text = text_input(outer, height=15)
        text.pack(fill='both', expand=True)
        for title,key in (("Motivo","motivo"),("Presión arterial","presion"),("Medicamentos / cambios","medicacion"),("Notas e indicaciones","notas")):
            text.insert('end', title + '\n' + (row[key] or 'Sin registrar') + '\n\n')
        text.configure(state='disabled')
