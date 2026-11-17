"""Preparación de Windows, separada de la interfaz y sin dependencias externas."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import venv


ENVIRONMENT = '.venv-windows'
READY_FILE = '.geforia-ready.json'
SETUP_VERSION = 1
RUNTIME_CHECK = 'import sys, tkinter; sys.exit(sys.version_info < (3, 10))'
DEPENDENCY_CHECK = 'import tkinter, serial'


def succeeds(command):
    result = subprocess.run(command, capture_output=True, text=True)
    return result.returncode == 0


def preparation_key(requirements):
    return {
        'setup_version': SETUP_VERSION,
        'requirements_sha256': hashlib.sha256(requirements.read_bytes()).hexdigest(),
    }


def prepare_environment(project):
    """Una marca solo es válida después de instalar y comprobar los requisitos."""
    environment = project / ENVIRONMENT
    python = environment / 'Scripts' / 'python.exe'
    requirements = project / 'requirements.txt'
    ready = environment / READY_FILE
    key = preparation_key(requirements)
    try:
        prepared = json.loads(ready.read_text(encoding='utf-8')) == key
    except (OSError, ValueError):
        prepared = False

    runtime_ok = python.is_file() and succeeds([str(python), '-c', RUNTIME_CHECK])
    if prepared and runtime_ok and succeeds([str(python), '-c', DEPENDENCY_CHECK]):
        return python

    # Invalidar la marca antes de trabajar: cualquier interrupción permite reintentar.
    ready.unlink(missing_ok=True)
    print('Preparando GeFORIA para Windows. La primera vez necesita Internet.', flush=True)
    if not runtime_ok:
        # Reparar en el mismo directorio, sin clear=True ni borrar otros archivos.
        venv.EnvBuilder(with_pip=True).create(environment)
    if not succeeds([str(python), '-c', RUNTIME_CHECK]):
        raise RuntimeError('El entorno no puede cargar Python 3.10 o posterior con Tkinter.')
    if not succeeds([str(python), '-m', 'pip', '--version']):
        subprocess.run([str(python), '-m', 'ensurepip', '--upgrade'], check=True)
    subprocess.run(
        [str(python), '-m', 'pip', 'install', '--disable-pip-version-check', '--no-input',
         '--force-reinstall',
         '-r', str(requirements)],
        check=True,
    )
    subprocess.run([str(python), '-m', 'pip', 'check', '--disable-pip-version-check'], check=True)
    if not succeeds([str(python), '-c', DEPENDENCY_CHECK]):
        raise RuntimeError('No se pudieron cargar Tkinter y pyserial después de la instalación.')
    pending = ready.with_suffix('.tmp')
    pending.write_text(json.dumps(key), encoding='utf-8')
    pending.replace(ready)
    print('Preparacion terminada. Las siguientes veces no se reinstalaran los complementos.',
          flush=True)
    return python


def main(argv=None):
    project = Path(__file__).resolve().parents[1]
    arguments = list(sys.argv[1:] if argv is None else argv)
    try:
        python = prepare_environment(project)
        # Se conserva el directorio del usuario y cada argumento, incluidos los espacios.
        return subprocess.run([str(python), str(project / 'main.py'), *arguments]).returncode
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f'\nNo se pudo preparar o abrir GeFORIA: {exc}', file=sys.stderr)
        print('Comprueba Internet y que la carpeta permita guardar archivos. '
              'Cierra otras ventanas de GeFORIA y vuelve a abrir iniciar_geforia.bat.\n'
              'No borres tus datos. Consulta GUIA_WINDOWS.md.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
