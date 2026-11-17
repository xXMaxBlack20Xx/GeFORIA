"""Vista guiada de conexión, adquisición y guardado."""
import sqlite3
import time
import tkinter as tk
from tkinter import ttk, messagebox
from ..services.serial_connection import available_ports
from .widgets import ScrollFrame, FormField, button, label
from .plot import SignalPlot
from . import theme


class MeasurementPage(ttk.Frame):
    def __init__(self,parent,app):
        super().__init__(parent)
        self.app = app
        self.notice = ''
        self.started = None
        self.plot_revision = None
        self.was_running = False
        label(self, 'Una medición, paso a paso', 'Title.TLabel').pack(anchor='w')
        self.person = label(self, '', 'Muted.TLabel')
        self.person.pack(anchor='w', pady=(5, 12))
        self.status = label(self, '', 'Banner.TLabel', wraplength=820)
        self.status.pack(fill='x', pady=(0, 10))
        actions = ttk.Frame(self)
        actions.pack(side='bottom', fill='x', pady=(12, 0))
        self.start_button = button(actions, 'Iniciar prueba · 60 s', self.start, primary=True)
        self.start_button.pack(side='left', padx=(0, 8))
        self.disconnect_button = button(actions, 'Desconectar', self.disconnect)
        self.disconnect_button.pack(side='left')
        self.save_button = button(actions, 'Guardar medición', self.save, primary=True)
        self.save_button.pack(side='right')
        self.scroll = ScrollFrame(self)
        self.scroll.pack(fill='both', expand=True)
        inner = self.scroll.content
        label(inner, '1  Conecta el dispositivo', 'Heading.TLabel').pack(anchor='w', pady=(0, 12))
        connection = ttk.Frame(inner, style='Card.TFrame')
        connection.pack(fill='x')
        self.method = tk.StringVar(value='USB')
        method = FormField(connection, 'Conexión', self.method, choices=('USB', 'Bluetooth SPP'), readonly=True)
        method.grid(row=0, column=0, sticky='new', padx=(0, 15))
        self.port = tk.StringVar()
        port = FormField(connection, 'Puerto del ESP32', self.port, choices=(),
                         help_text='COM en Windows; /dev/tty… en Linux. También puedes escribirlo.')
        port.input.configure(width=24)
        port.grid(row=0, column=1, sticky='new', padx=(0, 15))
        self.port_input = port.input
        commands = ttk.Frame(connection, style='Card.TFrame')
        commands.grid(row=1, column=0, columnspan=2, sticky='w', pady=(0, 10))
        button(commands, 'Buscar puertos', self.refresh_ports).pack(side='left', padx=(0, 8))
        self.connect_button = button(commands, 'Conectar', self.connect, primary=True)
        self.connect_button.pack(side='left')
        connection.columnconfigure(0, weight=1)
        connection.columnconfigure(1, weight=2)
        self.connection_hint = label(inner, 'Bluetooth: empareja el ESP32 en el sistema y elige su puerto serie saliente.', 'CardMuted.TLabel', wraplength=800)
        self.connection_hint.pack(anchor='w', pady=(0, 16))
        self.method.trace_add('write', lambda *_: self._method_hint())
        label(inner, '2  Coloca el dedo y comienza la prueba', 'Heading.TLabel').pack(anchor='w', pady=(0, 6))
        label(inner, 'Mantén la mano apoyada y el dedo quieto. La prueba termina cuando el ESP32 envía el resultado.', 'CardMuted.TLabel', wraplength=850).pack(anchor='w', pady=(0, 12))
        metrics = ttk.Frame(inner, style='Card.TFrame')
        metrics.pack(fill='x', pady=(0, 12))
        self.metrics = []
        for i,(title,subtitle) in enumerate((("Frecuencia cardíaca","BPM"),("Índice b/a","Exploratorio"),("Índice AGI","Exploratorio"))):
            card = ttk.Frame(metrics, style='Card.TFrame', padding=(10, 5))
            card.grid(row=0, column=i, sticky='ew')
            metrics.columnconfigure(i, weight=1)
            label(card, title, 'CardMuted.TLabel').pack(anchor='w')
            value = label(card, '—', 'Metric.TLabel')
            value.pack(anchor='w', pady=3)
            label(card, subtitle, 'CardMuted.TLabel').pack(anchor='w')
            self.metrics.append(value)
        self.progress = ttk.Progressbar(inner, mode='indeterminate')
        self.progress.pack(fill='x', pady=(0, 4))
        self.elapsed = label(inner, 'Sin prueba en curso.', 'CardMuted.TLabel')
        self.elapsed.pack(anchor='w', pady=(0, 10))
        self.plot = SignalPlot(inner)
        self.plot.pack(fill='both', expand=True)
        label(inner, '3  Revisa y guarda', 'Heading.TLabel').pack(anchor='w', pady=(12, 8))
        self.observations = tk.StringVar()
        self.observation_field=FormField(inner,"Observaciones de esta medición (opcional)",self.observations,
            help_text="Se guardan los últimos 30 s disponibles de PPG y SDPTG, junto con los índices recibidos.")
        self.observation_field.pack(fill='x')
        label(inner, 'Prototipo de investigación. Los resultados no constituyen un diagnóstico.', 'CardMuted.TLabel', wraplength=820).pack(anchor='w', pady=(10, 0))
        self.refresh_ports()
        self._method_hint()
        self.update_state()
        self.bind('<Configure>', lambda e: self.status.configure(wraplength=max(200, e.width - 30)) if e.widget is self else None)

    def _method_hint(self):
        self.connection_hint.configure(text="Bluetooth: empareja el ESP32 y selecciona su puerto serie saliente (SPP)." if self.method.get()=="Bluetooth SPP" else
            "USB: conecta el ESP32, busca los puertos y selecciona el que le corresponde.")

    def refresh_ports(self):
        try:
            ports = ['DEMO'] if self.app.demo else available_ports()
        except OSError as exc:
            self.notice = f'No se pudieron buscar puertos: {exc}'
            self.status.configure(text=self.notice, foreground=theme.ERROR)
            return
        self.port_input.configure(values=ports)
        if not self.port.get() and ports:
            self.port.set(ports[0])

    def _discard_capture(self):
        session = self.app.session
        if session.snapshot() is not None and not session.saved:
            return messagebox.askokcancel('Captura sin guardar', 'La captura actual no está guardada. ¿Descartarla para iniciar otra?', parent=self, default='cancel')
        return True

    def connect(self):
        if not self.port.get().strip():
            self.notice = 'Selecciona un puerto del ESP32 o escribe su nombre.'
            self.status.configure(text=self.notice, foreground=theme.ERROR)
            self.port_input.focus_set()
            return
        if not self._discard_capture():
            return
        session = self.app.session
        try:
            self.app.connection.connect(self.port.get().strip(), self.method.get() == 'Bluetooth SPP')
        except ValueError as exc:
            self.notice = str(exc)
            self.status.configure(text=self.notice, foreground=theme.ERROR)
            return
        self.notice = ''
        session.reset()
        session.connected = False
        session.connecting = True
        session.origin = 'DEMO' if self.app.demo else 'Bluetooth' if self.method.get() == 'Bluetooth SPP' else 'USB'
        session.message = 'Conectando el ESP32. Espera un momento…'
        self.observations.set('')
        self.plot_revision = None
        self.update_state()

    def start(self):
        if not self._discard_capture():
            return
        try:
            self.app.session.start()
            self.app.connection.start_test()
        except ValueError as exc:
            self.app.session.running = False
            self.notice = str(exc)
            self.status.configure(text=self.notice, foreground=theme.ERROR)
            return
        self.notice = ''
        self.started = time.monotonic()
        self.observations.set('')
        self.plot_revision = None
        self.update_state()

    def disconnect(self):
        self.notice = ''
        self.app.connection.disconnect()
        self.app.session.handle('disconnected', None)
        self.update_state()

    def save(self):
        capture = self.app.session.snapshot()
        if capture is not None and capture.quality!="Válida":
            text = 'El ESP32 indicó que se debe revisar la calidad.' if capture.quality == 'Revisar' else 'Esta es una captura parcial; no hay un resultado final del ESP32.'
            if not messagebox.askokcancel("Revisar captura",text+"\n¿Guardar con esta indicación en el historial?",parent=self,default="cancel"):
                return False
        try:
            self.app.session.save(self.app.database, self.app.records.active_id, self.observations.get())
        except (ValueError,sqlite3.Error) as exc:
            messagebox.showerror('No se pudo guardar', f'La captura sigue disponible.\n\n{exc}', parent=self)
            return False
        self.app.session.message = 'Medición guardada. Puedes consultarla en Historial o iniciar otra prueba.'
        self.app.history_page.refresh()
        self.update_state()
        return True

    def update_state(self):
        s = self.app.session
        profile = self.app.records.profile()
        self.person.configure(text=f"{profile['nombre']}  ·  {profile['id']}" if profile else 'Guarda tu expediente en Mis datos para poder guardar las mediciones.')
        if s.running:
            self.start_button.state(['disabled'])
        else:
            self.start_button.state(['!disabled'] if s.connected else ['disabled'])
        self.connect_button.state(['disabled'] if self.app.connection.busy or s.connecting else ['!disabled'])
        self.disconnect_button.state(['!disabled'] if self.app.connection.busy else ['disabled'])
        self.save_button.state(['!disabled'] if s.can_save and profile else ['disabled'])
        self.save_button.configure(text='Guardar medición' if s.completed else 'Guardar captura actual')
        self.status.configure(text=self.notice or s.message,foreground=theme.ERROR if self.notice else
                              (theme.WARNING if s.completed and not s.valid else theme.TEAL_DARK))
        for widget,value,precision in zip(self.metrics,(s.bpm,s.ba,s.agi),(0,3,3)):
            widget.configure(text=f'{value:.{precision}f}' if value is not None else '—')
        if s.running:
            if not self.was_running:
                self.progress.start(18)
            elapsed = int(time.monotonic() - self.started) if self.started is not None else 0
            self.elapsed.configure(text=f'{elapsed} s desde la solicitud · esperando el resultado del ESP32')
        else:
            if self.was_running:
                self.progress.stop()
            self.progress.configure(value=100 if s.completed else 0)
            self.elapsed.configure(text='Resultado recibido · calidad ' + ('válida' if s.valid else 'por revisar') if s.completed else 'Sin prueba en curso.')
        self.was_running = s.running
        revision = (s.revision, len(s.times))
        if self.winfo_ismapped() and revision!=self.plot_revision:
            self.plot.set_data(s.times, s.values, s.derivatives)
            self.plot_revision = revision
