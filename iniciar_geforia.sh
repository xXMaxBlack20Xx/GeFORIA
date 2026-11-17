#!/usr/bin/env bash
# Usa siempre el entorno del proyecto, sin depender del directorio actual.
set -u

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)" || exit 1
PYTHON="$PROJECT_DIR/.venv/bin/python"

if [[ ! -f "$PROJECT_DIR/main.py" ]]; then
    printf 'No se encuentra main.py junto a iniciar_geforia.sh. Conserva la carpeta completa del proyecto.\n' >&2
    exit 1
fi

if [[ ! -x "$PYTHON" ]]; then
    printf 'Falta el Python del entorno virtual de GeFORIA. Prepara el entorno con:\n' >&2
    printf '  cd %q\n' "$PROJECT_DIR" >&2
    printf '  python3 -m venv .venv\n  .venv/bin/python -m pip install -r requirements.txt\n' >&2
    printf 'En Fedora, si falta Tkinter: sudo dnf install python3-tkinter\n' >&2
    exit 1
fi

exec "$PYTHON" "$PROJECT_DIR/main.py" "$@"
