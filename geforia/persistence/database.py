"""Repositorio SQLite. Conserva tablas, columnas y señales comprimidas heredadas."""
import json
import math
import sqlite3
import zlib
from datetime import datetime
from pathlib import Path
from ..config import DATABASE_NAME, SCHEMA_VERSION, default_data_dir


class Database:
    """Persistencia local SQLite para pacientes y mediciones."""
    def __init__(self, path: str | Path | None = None):
        target = path if path is not None else default_data_dir() / DATABASE_NAME
        self.path = None if str(target) == ':memory:' else Path(target).expanduser()
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path) if self.path is not None else ':memory:')
        try:
            self.conn.execute('PRAGMA foreign_keys=ON')
            self._backup_before_migration()
            self.conn.executescript('''
                BEGIN;
                CREATE TABLE IF NOT EXISTS pacientes (
                    id TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    edad INTEGER NOT NULL,
                    peso REAL,
                    grasa REAL,
                    medicamentos TEXT DEFAULT '',
                    notas TEXT DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS mediciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paciente_id TEXT NOT NULL REFERENCES pacientes(id),
                    fecha TEXT NOT NULL,
                    bpm REAL,
                    estado TEXT NOT NULL,
                    descripcion TEXT NOT NULL,
                    origen TEXT NOT NULL
                );
            ''')
            # Migración no destructiva: conservar registros de versiones anteriores.
            existentes = {r[1] for r in self.conn.execute('PRAGMA table_info(pacientes)')}
            for campo, tipo in [('sexo','TEXT'), ('pas','REAL'), ('pad','REAL'),
                                ('antecedentes','TEXT'), ('tabaquismo','TEXT'),
                                ('actividad','TEXT'), ('temperatura','REAL')]:
                if campo not in existentes:
                    self.conn.execute(f'ALTER TABLE pacientes ADD COLUMN {campo} {tipo}')
            existentes_m = {r[1] for r in self.conn.execute('PRAGMA table_info(mediciones)')}
            for campo, tipo in [('calidad','TEXT'), ('indice_ba','REAL'), ('agi','REAL'), ('observaciones','TEXT')]:
                if campo not in existentes_m:
                    self.conn.execute(f'ALTER TABLE mediciones ADD COLUMN {campo} {tipo}')
            self.conn.execute('''CREATE TABLE IF NOT EXISTS senales_ppg (
                medicion_id INTEGER PRIMARY KEY REFERENCES mediciones(id) ON DELETE CASCADE,
                muestras BLOB NOT NULL, frecuencia_muestreo REAL,
                duracion REAL NOT NULL
            )''')
            self.conn.execute('CREATE TABLE IF NOT EXISTS geforia_config (clave TEXT PRIMARY KEY, valor TEXT)')
            self.conn.execute('''CREATE TABLE IF NOT EXISTS consultas_geforia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id TEXT NOT NULL REFERENCES pacientes(id),
                fecha TEXT NOT NULL, motivo TEXT, notas TEXT, medicacion TEXT, presion TEXT
            )''')
            self.conn.execute("INSERT OR REPLACE INTO geforia_config(clave,valor) VALUES('app_schema_version',?)", (SCHEMA_VERSION,))
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            self.conn.close()
            raise

    def guardar_paciente(self, datos, *, activate=False):
        columnas = ('id','nombre','edad','peso','medicamentos','notas','sexo','pas',
                    'pad','antecedentes','tabaquismo','actividad','temperatura')
        campos = ','.join(columnas)
        placeholders = ','.join(('?' for _ in columnas))
        actualizaciones = ','.join((f'{c}=excluded.{c}' for c in columnas if c != 'id'))
        with self.conn:
            self.conn.execute(f"INSERT INTO pacientes({campos}) VALUES({placeholders}) "
                              f"ON CONFLICT(id) DO UPDATE SET {actualizaciones}", datos)
            if activate:
                self.conn.execute("INSERT OR REPLACE INTO geforia_config(clave,valor) VALUES('paciente_id',?)", (datos[0],))


    def paciente(self, pid):
        return self.conn.execute('SELECT * FROM pacientes WHERE id=?', (pid,)).fetchone()

    def guardar_medicion(self, pid, bpm, estado, descripcion, origen, calidad, ba, agi, observaciones, senal=None):
        if senal is not None:
            tiempos, valores, segundas = senal
            if len(tiempos) < 2 or not len(tiempos) == len(valores) == len(segundas):
                raise ValueError('La señal debe contener al menos dos muestras y columnas del mismo tamaño.')
            if (not all(math.isfinite(t) for t in tiempos)
                    or not all(math.isfinite(v) for v in valores)
                    or not all(b > a for a, b in zip(tiempos, tiempos[1:]))
                    or not all(d is None or math.isfinite(d) for d in segundas)):
                raise ValueError('La señal contiene tiempos o valores no válidos.')
        with self.conn:
            cursor = self.conn.execute('''INSERT INTO mediciones(paciente_id,fecha,bpm,estado,descripcion,origen,calidad,indice_ba,agi,observaciones)
                VALUES(?,?,?,?,?,?,?,?,?,?)''', (pid, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        bpm, estado, descripcion, origen, calidad, ba, agi, observaciones))
            if senal is not None:
                tiempos, valores, segundas = senal
                if len(tiempos) >= 2 and len(tiempos) == len(valores) == len(segundas):
                    duracion = float(tiempos[-1] - tiempos[0])
                    if duracion > 0:
                        payload = json.dumps({'t': tiempos, 'y': valores, 'sdptg': segundas}, separators=(',', ':'), allow_nan=False).encode('utf-8')
                        self.conn.execute('''INSERT INTO senales_ppg(medicion_id,muestras,frecuencia_muestreo,duracion)
                            VALUES(?,?,?,?)''', (cursor.lastrowid, sqlite3.Binary(zlib.compress(payload)),
                            (len(tiempos)-1)/duracion, duracion))

    def historial(self):
        return self.conn.execute('''SELECT m.fecha,p.id,p.nombre,m.bpm,m.estado,m.descripcion,m.origen,m.calidad,m.indice_ba,m.agi,m.observaciones
            FROM mediciones m JOIN pacientes p ON p.id=m.paciente_id
            ORDER BY m.id DESC LIMIT 1000''').fetchall()

    def listar_pacientes(self):
        '''Lista todos los pacientes, incluso sin estudios asociados.'''
        return self.conn.execute('''SELECT p.id, p.nombre, p.edad, p.sexo,
                p.pas, p.pad, COUNT(m.id) AS estudios
                FROM pacientes p LEFT JOIN mediciones m ON m.paciente_id = p.id
                GROUP BY p.id ORDER BY p.nombre COLLATE NOCASE''').fetchall()

    def detalle_paciente(self, pid):
        '''Recupera los campos clínicos usando sus nombres de columna.'''
        cursor = self.conn.execute('SELECT * FROM pacientes WHERE id=?', (pid,))
        fila = cursor.fetchone()
        return dict(zip((c[0] for c in cursor.description), fila)) if fila else None

    def historial_paciente(self, pid=None):
        '''Estudios de un paciente, o todos si no se proporciona un ID.'''
        consulta = '''SELECT m.fecha,p.id,p.nombre,m.bpm,m.estado,m.descripcion,
                    m.origen,m.calidad,m.indice_ba,m.agi,m.observaciones
                    FROM mediciones m JOIN pacientes p ON p.id=m.paciente_id'''
        parametros = ()
        if pid:
            consulta += ' WHERE p.id=?'
            parametros = (pid,)
        consulta += ' ORDER BY m.id DESC LIMIT 1000'
        return self.conn.execute(consulta, parametros).fetchall()

    def ids_estudios(self, pid=None):
        """IDs de estudios en el mismo orden que historial_paciente."""
        consulta = 'SELECT id FROM mediciones'
        parametros = ()
        if pid:
            consulta += ' WHERE paciente_id=?'
            parametros = (pid,)
        consulta += ' ORDER BY id DESC LIMIT 1000'
        return [fila[0] for fila in self.conn.execute(consulta, parametros)]

    def obtener_senal(self, estudio_id):
        fila = self.conn.execute('SELECT muestras FROM senales_ppg WHERE medicion_id=?', (estudio_id,)).fetchone()
        if not fila:
            return None
        datos = json.loads(zlib.decompress(fila[0]).decode('utf-8'))
        return (datos['t'], datos.get('sdptg'))

    def estudios_con_senal(self, pid):
        return self.conn.execute('''SELECT m.id, m.fecha, m.bpm, m.origen
            FROM mediciones m JOIN senales_ppg s ON s.medicion_id=m.id
            WHERE m.paciente_id=? ORDER BY m.id DESC LIMIT 100''', (pid,)).fetchall()

    def eliminar_estudio(self, estudio_id):
        """Elimina solo una medición; conserva el paciente y otros estudios."""
        with self.conn:
            self.conn.execute('DELETE FROM senales_ppg WHERE medicion_id=?', (estudio_id,))
            resultado = self.conn.execute('DELETE FROM mediciones WHERE id=?', (estudio_id,))
        return resultado.rowcount

    def eliminar_paciente(self, pid):
        """Elimina un paciente y sus estudios en una única transacción."""
        with self.conn:
            self.conn.execute('DELETE FROM consultas_geforia WHERE paciente_id=?', (pid,))
            self.conn.execute("DELETE FROM geforia_config WHERE clave='paciente_id' AND valor=?", (pid,))
            self.conn.execute('DELETE FROM senales_ppg WHERE medicion_id IN (SELECT id FROM mediciones WHERE paciente_id=?)', (pid,))
            self.conn.execute('DELETE FROM mediciones WHERE paciente_id=?', (pid,))
            resultado = self.conn.execute('DELETE FROM pacientes WHERE id=?', (pid,))
        return resultado.rowcount

    def cerrar(self):
        self.conn.close()

    def _backup_before_migration(self):
        tables = {row[0] for row in self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'pacientes' not in tables or self.path is None:
            return
        version = self.conn.execute("SELECT valor FROM geforia_config WHERE clave='app_schema_version'").fetchone() if 'geforia_config' in tables else None
        if version and version[0] == SCHEMA_VERSION:
            return
        folder = self.path.parent / 'backups'
        folder.mkdir(exist_ok=True)
        suffix = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        target = folder / f'registros_antes_v3_{suffix}.sqlite3'
        with sqlite3.connect(target) as dest:
            self.conn.backup(dest)

    def active_id(self):
        row = self.conn.execute("SELECT valor FROM geforia_config WHERE clave='paciente_id'").fetchone()
        return row[0] if row and self.paciente(row[0]) else None

    def activate_profile(self, pid):
        if not self.paciente(pid):
            raise ValueError('El expediente seleccionado no existe.')
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO geforia_config(clave,valor) VALUES('paciente_id',?)", (pid,))

    def studies(self, pid):
        cursor = self.conn.execute('SELECT * FROM mediciones WHERE paciente_id=? ORDER BY id DESC LIMIT 1000', (pid,))
        names = [col[0] for col in cursor.description]
        return [dict(zip(names, row)) for row in cursor]

    def signal_detail(self, study_id):
        row = self.conn.execute('SELECT muestras FROM senales_ppg WHERE medicion_id=?', (study_id,)).fetchone()
        return json.loads(zlib.decompress(row[0]).decode('utf-8')) if row else None

    def consultations(self, pid):
        cursor = self.conn.execute('SELECT * FROM consultas_geforia WHERE paciente_id=? ORDER BY id DESC', (pid,))
        names = [col[0] for col in cursor.description]
        return [dict(zip(names, row)) for row in cursor]

    def save_consultation(self, pid, values):
        with self.conn:
            self.conn.execute('INSERT INTO consultas_geforia(paciente_id,fecha,motivo,notas,medicacion,presion) VALUES(?,?,?,?,?,?)',
                (pid, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), values['motivo'], values['notas'], values['medicacion'], values['presion']))

    def backup(self, destination):
        if self.path is not None and Path(destination).resolve() == self.path.resolve():
            raise ValueError('Elige un archivo distinto de la base activa.')
        with sqlite3.connect(destination) as target:
            self.conn.backup(target)

