"""Componentes compartidos y navegación por teclado."""
import tkinter as tk
from tkinter import ttk
from weakref import WeakSet
from . import theme


def label(parent, text, style="TLabel", **kwargs):
    if 'wraplength' not in kwargs and len(text) > 60:
        kwargs['wraplength'] = 800
    widget = ttk.Label(parent, text=text, style=style, **kwargs)
    if 'wraplength' in kwargs:
        widget.configure(justify=kwargs.get('justify', 'left'))
        def fit(event):
            if widget.winfo_exists():
                widget.configure(wraplength=max(120, event.width - 32))
        parent.bind('<Configure>', fit, add='+')
    return widget


def button(parent, text, command, primary=False, **kwargs):
    return ttk.Button(parent, text=text, command=command,
                      style="Primary.TButton" if primary else "TButton", **kwargs)


def text_input(parent, height=4):
    widget = tk.Text(parent, height=height, wrap="word", background=theme.SURFACE,
                     foreground=theme.TEXT, insertbackground=theme.TEXT, relief="flat",
                     highlightthickness=1, highlightbackground=theme.BORDER,
                     highlightcolor=theme.TEAL, padx=10, pady=8, undo=True,
                     font=(theme.FONT, 10))
    # Tab recorre el formulario; Ctrl+Tab inserta tabulación si se necesita.
    def next_widget(event):
        event.widget.tk_focusNext().focus_set()
        return 'break'
    def previous_widget(event):
        event.widget.tk_focusPrev().focus_set()
        return 'break'
    widget.bind('<Tab>', next_widget)
    widget.bind('<Shift-Tab>', previous_widget)
    widget.bind('<ISO_Left_Tab>', previous_widget)
    return widget


class ScrollFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style='Card.TFrame')
        self.canvas = tk.Canvas(self, background=theme.SURFACE, highlightthickness=0, takefocus=False)
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.content = ttk.Frame(self.canvas, style='Card.TFrame', padding=20)
        self.window = self.canvas.create_window((0, 0), window=self.content, anchor='nw')
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.content.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfigure(self.window, width=e.width))
        root = self
        while root.master is not None:
            root = root.master
        if not hasattr(root, "_scroll_frames"):
            root._scroll_frames = WeakSet()
            for event in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                root.bind_all(event, lambda e, r=root: ScrollFrame._route(r, e, False), add='+')
            root.bind_all('<FocusIn>', lambda e, r=root: ScrollFrame._route(r, e, True), add='+')
        root._scroll_frames.add(self)
        self._event_root = root

    @staticmethod
    def _route(root, event, focus):
        for frame in list(root._scroll_frames):
            if frame.winfo_exists():
                frame._focus(event) if focus else frame._wheel(event)

    def _contains(self, widget):
        while widget is not None:
            if widget is self.content or widget is self.canvas:
                return True
            widget = getattr(widget, 'master', None)
        return False

    def _wheel(self, event):
        if self.winfo_ismapped() and self._contains(event.widget):
            if isinstance(event.widget, tk.Text) and event.widget.yview() != (0., 1.):
                return
            if self.canvas.yview() == (0., 1.):
                return
            direction = -1 if getattr(event, 'num', None) == 4 or getattr(event, 'delta', 0) > 0 else 1
            self.canvas.yview_scroll(direction * 3, 'units')

    def _focus(self, event):
        if self.winfo_ismapped() and self._contains(event.widget) and isinstance(event.widget, (ttk.Entry, ttk.Combobox, tk.Text, ttk.Button)):
            self._event_root.after_idle(lambda w=event.widget: self.reveal(w) if self.winfo_exists() and w.winfo_exists() else None)

    def reveal(self, widget):
        self.update_idletasks()
        top = widget.winfo_rooty() - self.content.winfo_rooty()
        total = max(1, self.content.winfo_height())
        visible_top = self.canvas.canvasy(0)
        visible_bottom = visible_top + self.canvas.winfo_height()
        bottom = top + widget.winfo_height() + 30
        if top < visible_top:
            self.canvas.yview_moveto(max(0, top - 30) / total)
        elif bottom > visible_bottom:
            self.canvas.yview_moveto(max(0, bottom - self.canvas.winfo_height()) / total)


class FormField(ttk.Frame):
    def __init__(self, parent, title, variable, *, required=False, help_text="",
                 choices=None, readonly=False):
        super().__init__(parent, style='Card.TFrame')
        label(self, title + (' *' if required else ''), 'Card.TLabel').pack(anchor='w', pady=(0, 5))
        if choices is not None:
            self.input = ttk.Combobox(self, textvariable=variable, values=choices,
                                      state="readonly" if readonly else "normal", width=20)
        else:
            self.input = ttk.Entry(self, textvariable=variable, width=20)
            if readonly:
                self.input.state(['readonly'])
        self.input.pack(fill='x')
        if help_text:
            self.help = label(self, help_text, 'CardMuted.TLabel', wraplength=380, font=(theme.FONT, 9))
            self.help.pack(anchor='w', pady=(5, 0))
            self.bind('<Configure>', lambda e: self.help.configure(wraplength=max(120, e.width)), add='+')
        self.error = label(self, '', 'Error.TLabel', wraplength=380)
        self.error.pack(anchor='w', pady=(3, 0))

    def set_error(self, message=""):
        self.error.configure(text=message)
        self.input.state(['invalid'] if message else ['!invalid'])


def table(parent, columns, height=8):
    """Tabla con desplazamiento en ambos ejes y selección simple."""
    frame = ttk.Frame(parent, style='Card.TFrame')
    view = ttk.Treeview(frame, columns=tuple(c[0] for c in columns), show="headings",
                        height=height, selectmode="browse")
    for key, title, width in columns:
        view.heading(key, text=title)
        view.column(key, width=width, minwidth=75, stretch=True)
    vertical = ttk.Scrollbar(frame, orient='vertical', command=view.yview)
    horizontal = ttk.Scrollbar(frame, orient='horizontal', command=view.xview)
    view.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    view.grid(row=0, column=0, sticky='nsew')
    vertical.grid(row=0, column=1, sticky='ns')
    horizontal.grid(row=1, column=0, sticky='ew')
    return (frame, view)
