"""Configuración compartida, sin crear archivos al importar."""
from pathlib import Path

APP_NAME = 'GeFORIA'
DATABASE_NAME = 'registros.sqlite3'
BAUDRATE = 921600
SAMPLE_RATE = 200.0
BUFFER_SIZE = 13000  # 65 s; se conservan 30 s al guardar, como en el original.
VISIBLE_SECONDS = 8.0
SAVED_SECONDS = 30.0
POLL_MS = 100
SCHEMA_VERSION = '2'


def default_data_dir() -> Path:
    return Path.home() / 'GeFORIA'
