"""Captura progresiva del expediente, con borrador conservado entre páginas."""
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from ..models import Profile
from ..validation import IDENTITY_FIELDS, HEALTH_FIELDS, ValidationError, validate_profile
from .widgets import ScrollFrame, FormField, button, label, text_input
from . import theme

FIELD_TITLES = {
    "id":"Código del expediente", "nombre":"Nombre completo", "edad":"Edad (años)",
    "sexo":"Sexo", "peso":"Peso (kg)", "pas":"Presión sistólica (mmHg)",
    "pad":"Presión diastólica (mmHg)", "temperatura":"Temperatura del dedo (°C)",
    "antecedentes":"Antecedentes cardiovasculares", "tabaquismo":"Tabaquismo",
    "actividad":"Actividad física reciente", "medicamentos":"Medicamentos actuales", "notas":"Notas generales"}


class ProfilePage(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app, self.service = (app, app.records)
        self.loading, self.dirty, self.step = (False, False, 0)
        self.vars = {key: tk.StringVar() for key in Profile.__dataclass_fields__ if key != 'notas'}
        self.fields, self.initial = ({}, {})
        label(self, 'Tu expediente personal', 'Title.TLabel').pack(anchor='w')
        label(self, 'Solo nombre y edad para empezar. El resto puedes completarlo después.', 'Muted.TLabel').pack(anchor='w', pady=(5, 14))
        self.banner = label(self, 'Los campos con * son obligatorios. Tu código se genera automáticamente.', 'Banner.TLabel', wraplength=850)
        self.banner.pack(fill='x', pady=(0, 12))
        self.legacy = ttk.Frame(self, padding=12, style='Card.TFrame')
        self.legacy_map = {}
        if not self.service.active_id:
            for row in app.database.listar_pacientes():
                self.legacy_map[f'{row[1]} · {row[0]}'] = row[0]
        if self.legacy_map:
            self.legacy.pack(fill='x', pady=(0, 10))
            label(self.legacy, 'Se encontraron expedientes anteriores. Elige el tuyo para conservar su historial.', 'CardMuted.TLabel', wraplength=750).pack(anchor='w')
            row = ttk.Frame(self.legacy, style='Card.TFrame')
            row.pack(fill='x', pady=(8, 0))
            self.legacy_choice = ttk.Combobox(row, state='readonly', values=list(self.legacy_map), width=35)
            self.legacy_choice.pack(side='left', fill='x', expand=True, padx=(0, 10))
            button(row, 'Usar este expediente', self._activate_legacy).pack(side='right')
        steps = ttk.Frame(self)
        steps.pack(fill='x', pady=(0, 10))
        self.step_buttons = []
        for index, title in enumerate(("1  Datos básicos", "2  Salud · opcional", "3  Revisar")):
            btn = ttk.Button(steps, text=title, command=lambda i=index: self.go_step(i), style='Step.TButton')
            btn.pack(side='left', fill='x', expand=True, padx=(0, 8 if index < 2 else 0))
            self.step_buttons.append(btn)
        footer = ttk.Frame(self)
        footer.pack(side='bottom', fill='x', pady=(12, 0))
        self.previous = button(footer, 'Anterior', lambda: self.go_step(self.step - 1))
        self.previous.pack(side='left')
        self.next = button(footer, 'Siguiente', lambda: self.go_step(self.step + 1))
        self.next.pack(side='left', padx=8)
        self.save_button = button(footer, 'Guardar expediente', self.save, primary=True)
        self.save_button.pack(side='right')
        self.dirty_label = label(footer, '', 'Muted.TLabel')
        self.dirty_label.pack(side='right', padx=12)
        self.progress = ttk.Progressbar(self, maximum=3, value=1)
        self.progress.pack(side='bottom', fill='x')
        self.scroll = ScrollFrame(self)
        self.scroll.pack(fill='both', expand=True)
        self.pages = [ttk.Frame(self.scroll.content, style='Card.TFrame') for _ in range(3)]
        self._basic_fields()
        self._health_fields()
        self._review_fields()
        for variable in self.vars.values():
            variable.trace_add('write', lambda *_: self._changed())
        self.notes.bind('<<Modified>>', self._notes_changed)
        self.load()
        self.go_step(0, validate=False)
        self.bind('<Configure>', self._resize, add='+')

    def _add_field(self, parent, key, row, col, **kwargs):
        field = FormField(parent, FIELD_TITLES[key], self.vars[key], **kwargs)
        field.grid(row=row, column=col, sticky='new', padx=(0, 18 if col == 0 else 0), pady=(0, 10))
        self.fields[key] = field
        field.input.bind('<FocusOut>', lambda e, k=key: self._validate_field(k), add='+')
        parent.columnconfigure(col, weight=1)

    def _basic_fields(self):
        page = self.pages[0]
        label(page, 'Lo esencial para comenzar', 'Heading.TLabel').pack(anchor='w', pady=(0, 16))
        grid = ttk.Frame(page, style='Card.TFrame')
        grid.pack(fill='x')
        self._add_field(grid, 'nombre', 0, 0, required=True, help_text='Usa el nombre que quieres ver en tu historial.')
        self._add_field(grid, 'edad', 0, 1, required=True, help_text='Años cumplidos. Por ejemplo: 30.')
        self._add_field(grid, 'sexo', 1, 0, choices=('', 'Femenino', 'Masculino', 'Otro', 'Prefiero no indicar'), readonly=True, help_text='Opcional; puedes dejarlo vacío.')
        self._add_field(grid, 'id', 1, 1, required=True, help_text='Ya está listo. Puedes personalizarlo antes del primer guardado.')
        label(page, '¿Tienes prisa? Guarda ahora y completa la información opcional cuando quieras.', 'CardMuted.TLabel', wraplength=750).pack(anchor='w', pady=(12, 0))

    def _health_fields(self):
        page = self.pages[1]
        label(page, 'Información de salud', 'Heading.TLabel').pack(anchor='w', pady=(0, 5))
        label(page, 'Todo es opcional. Registra solo los valores que conozcas; no se estiman automáticamente.', 'CardMuted.TLabel', wraplength=750).pack(anchor='w', pady=(0, 16))
        grid = ttk.Frame(page, style='Card.TFrame')
        grid.pack(fill='x')
        self._add_field(grid, 'peso', 0, 0, help_text='Acepta decimales: 72.5 o 72,5.')
        self._add_field(grid, 'temperatura', 0, 1, help_text='Temperatura del dedo, si la mediste.')
        self._add_field(grid, 'pas', 1, 0, help_text='El número superior. Ejemplo: 120.')
        self._add_field(grid, 'pad', 1, 1, help_text='El número inferior. Ejemplo: 80.')
        self._add_field(grid, 'tabaquismo', 2, 0, choices=('', 'Nunca', 'Anterior', 'Actual', 'Prefiero no indicar'), help_text='Selecciona una opción o escribe un detalle.')
        self._add_field(grid, 'actividad', 2, 1, choices=('', 'Sin actividad reciente', 'Ligera', 'Moderada', 'Intensa'), help_text='Selecciona una opción o escribe un detalle.')
        self._add_field(grid, 'antecedentes', 3, 0, help_text='Si no los conoces, deja este campo vacío.')
        self._add_field(grid, 'medicamentos', 3, 1, help_text='Nombre y dosis, si deseas registrarlos.')
        label(page, 'Notas generales del expediente', 'Card.TLabel').pack(anchor='w', pady=(8, 5))
        self.notes = text_input(page, height=4)
        self.notes.pack(fill='x')

    def _review_fields(self):
        page = self.pages[2]
        label(page, 'Revisa antes de guardar', 'Heading.TLabel').pack(anchor='w', pady=(0, 8))
        label(page, 'Puedes volver a cualquier sección para corregir un dato.', 'CardMuted.TLabel').pack(anchor='w', pady=(0, 12))
        self.summary = label(page, '', 'Card.TLabel', justify='left', wraplength=780)
        self.summary.pack(anchor='w', fill='x')
        button(page, 'Editar datos básicos', lambda: self.go_step(0)).pack(anchor='w', pady=(14, 0))

    def _resize(self, event):
        if event.widget is self:
            self.banner.configure(wraplength=max(250, event.width - 30))
            self.summary.configure(wraplength=max(250, event.width - 90))

    def values(self):
        values = {key: var.get() for key, var in self.vars.items()}
        values['notas'] = self.notes.get('1.0', 'end-1c')
        return values

    def load(self):
        self.loading = True
        data = self.service.profile() or {'id': self.service.new_code()}
        for key,var in self.vars.items():
            value = data.get(key)
            var.set('' if value is None else str(value))
        self.notes.delete('1.0', 'end')
        self.notes.insert('1.0', data.get('notas') or '')
        self.notes.edit_modified(False)
        self.fields['id'].input.state(['readonly'] if self.service.active_id else ['!readonly'])
        if self.service.active_id:
            self.fields['id'].help.configure(text='Código fijo: mantiene todas tus mediciones en el mismo expediente.')
        for field in self.fields.values():
            field.set_error()
        self.initial = self.values()
        self.loading = False
        self._changed()

    def _changed(self):
        if self.loading:
            return
        self.dirty = self.values() != self.initial
        self.dirty_label.configure(text='Cambios sin guardar' if self.dirty else '')
        if self.step==2:
            self._update_summary()

    def _notes_changed(self, event):
        if self.notes.edit_modified():
            self.notes.edit_modified(False)
            self._changed()

    def _validate_field(self,key):
        if self.loading:
            return
        errors = validate_profile(self.values(), self.service.active_id)
        self.fields[key].set_error(errors.get(key, ''))
        if key=="pas":
            self.fields['pad'].set_error(errors.get('pad', ''))

    def _show_errors(self,errors):
        for key,field in self.fields.items():
            field.set_error(errors.get(key, ''))
        if errors:
            first = next(iter(errors))
            self.go_step(0 if first in IDENTITY_FIELDS else 1, validate=False)
            self.banner.configure(text='Revisa los campos marcados antes de continuar.', foreground=theme.ERROR)
            self.fields[first].input.focus_set()
            self.scroll.reveal(self.fields[first].input)

    def go_step(self,index,validate=True):
        if not 0<=index<3:
            return False
        if validate and index>self.step:
            scope = IDENTITY_FIELDS if index == 1 else None
            errors = validate_profile(self.values(), self.service.active_id, only=scope)
            if errors:
                self._show_errors(errors)
                return False
        for page in self.pages:
            page.pack_forget()
        self.pages[index].pack(fill='both', expand=True)
        self.step = index
        for i,btn in enumerate(self.step_buttons):
            btn.configure(style='ActiveStep.TButton' if i == index else 'Step.TButton')
        self.previous.state(['disabled'] if index == 0 else ['!disabled'])
        self.next.state(['disabled'] if index == 2 else ['!disabled'])
        self.progress.configure(value=index + 1)
        self.scroll.canvas.yview_moveto(0)
        if index==2:
            self._update_summary()
        return True

    def _update_summary(self):
        values = self.values()
        sections=["DATOS BÁSICOS", *(f"{FIELD_TITLES[k]}: {values.get(k) or 'Sin registrar'}" for k in IDENTITY_FIELDS),
                  "", "INFORMACIÓN OPCIONAL", *(f"{FIELD_TITLES[k]}: {values.get(k) or 'Sin registrar'}" for k in HEALTH_FIELDS),
                  "", "Notas generales: "+(values["notas"] or "Sin registrar")]
        self.summary.configure(text='\n'.join(sections))

    def save(self):
        values = self.values()
        errors = validate_profile(values, self.service.active_id)
        if errors:
            self._show_errors(errors)
            return False
        if self.service.active_id and self.dirty:
            if not messagebox.askokcancel("Actualizar expediente", "¿Guardar los cambios de tu expediente? Tus mediciones y consultas se conservarán.", parent=self, default="cancel"):
                return False
        try:
            self.service.save_profile(values)
        except ValidationError as exc:
            self._show_errors(exc.errors)
            return False
        except sqlite3.Error as exc:
            messagebox.showerror('No se pudo guardar', f'Tus datos siguen en pantalla. Intenta guardar de nuevo.\n\n{exc}', parent=self)
            return False
        self.load()
        self.legacy.pack_forget()
        self.banner.configure(text='Expediente guardado. Ya puedes abrir Medición para registrar una prueba.', foreground=theme.TEAL_DARK)
        self.app.profile_saved()
        return True

    def _activate_legacy(self):
        code = self.legacy_map.get(self.legacy_choice.get())
        if not code:
            self.banner.configure(text='Selecciona tu expediente anterior en la lista.', foreground=theme.ERROR)
            return
        prompt = '¿Usar el expediente seleccionado como tu expediente personal?'
        if self.dirty:
            prompt += '\nEl borrador actual sin guardar se descartará.'
        if not messagebox.askokcancel("Seleccionar expediente",prompt,parent=self,default="cancel"):
            return
        try:
            self.service.activate(code)
        except (ValueError,sqlite3.Error) as exc:
            messagebox.showerror('Expediente', str(exc), parent=self)
            return
        self.load()
        self.legacy.pack_forget()
        self.app.profile_saved()
        self.banner.configure(text='Expediente recuperado con su historial anterior.', foreground=theme.TEAL_DARK)
