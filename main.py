"""Ejecuta GeFORIA. No cambia de directorio ni necesita rutas absolutas."""
import argparse
import logging
from pathlib import Path
import sqlite3
import sys
from geforia.config import default_data_dir


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='GeFORIA · Seguimiento personal PPG y SDPTG')
    parser.add_argument('--data-dir', type=Path, help='Carpeta de datos; por defecto ~/GeFORIA')
    parser.add_argument('--demo', action='store_true', help='Datos simulados en una carpeta demo independiente')
    args = parser.parse_args(argv)
    folder = (args.data_dir or default_data_dir()).expanduser()
    if args.demo:
        folder = folder / 'demo'
    logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
    try:
        import tkinter as tk
        from geforia.app import App
    except ImportError as exc:
        print(f'No se pudo cargar la interfaz: {exc}\nInstala Python con soporte Tkinter (Tk).', file=sys.stderr)
        return 1
    try:
        app = App(folder, demo=args.demo)
    except tk.TclError as exc:
        print(f'No se pudo abrir la ventana de GeFORIA: {exc}\nEjecuta el programa dentro de una sesión gráfica con Tkinter disponible.', file=sys.stderr)
        return 1
    except (sqlite3.Error,OSError) as exc:
        print(f'No se pudieron abrir los datos en {folder}: {exc}\nComprueba permisos y espacio disponible; puedes usar --data-dir CARPETA.', file=sys.stderr)
        return 1
    app.mainloop()
    return 0


if __name__=="__main__":
    raise SystemExit(main())
