"""Paleta y estilos compartidos."""
from tkinter import font, ttk

BG = '#F2F6F8'
SURFACE = '#FFFFFF'
NAVY = '#102D3A'
TEXT = '#173A48'
MUTED = '#526974'
TEAL = '#0B6B63'
TEAL_DARK = '#08564F'
SOFT = '#E1F2EF'
BORDER = '#C7D4DA'
ERROR = '#B42318'
ERROR_BG = '#FFF1EF'
WARNING = '#8A4B00'
FONT = 'TkDefaultFont'


def configure_theme(root):
    global FONT
    families = set(font.families(root))
    FONT = next((family for family in ("Inter", "Segoe UI", "Noto Sans", "DejaVu Sans")
                 if family in families), "TkDefaultFont")
    font.nametofont('TkDefaultFont').configure(family=FONT, size=10)
    font.nametofont('TkTextFont').configure(family=FONT, size=10)
    root.option_add('*Font', (FONT, 10))
    root.option_add('*TCombobox*Listbox.font', (FONT, 10))
    root.configure(background=BG)
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', font=(FONT, 10), background=BG, foreground=TEXT)
    style.configure('TFrame', background=BG)
    style.configure('Card.TFrame', background=SURFACE)
    style.configure('TLabel', background=BG, foreground=TEXT)
    style.configure('Card.TLabel', background=SURFACE)
    style.configure('Muted.TLabel', foreground=MUTED)
    style.configure('CardMuted.TLabel', background=SURFACE, foreground=MUTED)
    style.configure('Title.TLabel', font=(FONT, 22, 'bold'))
    style.configure('Heading.TLabel', font=(FONT, 13, 'bold'), background=SURFACE)
    style.configure('Metric.TLabel', font=(FONT, 24, 'bold'), foreground=TEAL, background=SURFACE)
    style.configure('Error.TLabel', foreground=ERROR, background=SURFACE, font=(FONT, 9))
    style.configure('Banner.TLabel', background=SOFT, foreground=TEAL_DARK, padding=(12, 9))
    style.configure("TButton", padding=(14, 10), background=SURFACE, foreground=TEXT,
                    bordercolor=BORDER, focusthickness=2, focuscolor=TEAL)
    style.map('TButton', background=[('active', SOFT)], foreground=[('disabled', '#6B7B83')])
    style.configure("Primary.TButton", background=TEAL, foreground="white", bordercolor=TEAL,
                    font=(FONT, 10, "bold"), focuscolor="#FFFFFF")
    style.map("Primary.TButton", background=[("disabled", "#CBD6D8"), ("active", TEAL_DARK)],
              foreground=[("disabled", "#52636B"), ("!disabled", "#FFFFFF")])
    style.configure('Danger.TButton', foreground=ERROR)
    style.configure('Step.TButton', padding=(12, 9))
    style.configure("ActiveStep.TButton", background=SOFT, foreground=TEAL_DARK, bordercolor=TEAL,
                    font=(FONT, 10, "bold"))
    style.configure("TEntry", padding=(9, 9), fieldbackground=SURFACE, foreground=TEXT,
                    bordercolor=BORDER, insertcolor=TEXT)
    style.map("TEntry", bordercolor=[("invalid", ERROR), ("focus", TEAL)],
              fieldbackground=[("invalid", ERROR_BG), ("readonly", "#E9EFF2")])
    style.configure("TCombobox", padding=(8, 8), fieldbackground=SURFACE, foreground=TEXT,
                    bordercolor=BORDER, arrowsize=16)
    style.map("TCombobox", fieldbackground=[("readonly", SURFACE), ("invalid", ERROR_BG)],
              foreground=[("readonly", TEXT)], bordercolor=[("invalid", ERROR), ("focus", TEAL)])
    style.configure("Treeview", background=SURFACE, fieldbackground=SURFACE, foreground=TEXT,
                    rowheight=36, bordercolor=BORDER)
    style.configure("Treeview.Heading", background="#E8EFF2", foreground=TEXT,
                    font=(FONT, 10, "bold"), padding=(8, 9))
    style.map('Treeview', background=[('selected', SOFT)], foreground=[('selected', TEAL_DARK)])
    style.configure('TNotebook', background=BG, borderwidth=0)
    style.configure('TNotebook.Tab', padding=(18, 10))
    style.map('TNotebook.Tab', background=[('selected', SURFACE)], foreground=[('selected', TEAL)])
    style.configure('Horizontal.TProgressbar', background=TEAL, troughcolor=SOFT, borderwidth=0)
