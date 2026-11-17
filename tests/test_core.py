from contextlib import closing
import math
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from geforia.persistence.database import Database
from geforia.services.acquisition import AcquisitionSession
from geforia.services.protocol import LineBuffer, parse_line
from geforia.services.records import RecordService
from geforia.services.signal_processing import filtrar_ppg
from geforia.validation import make_profile, validate_profile, ValidationError, IDENTITY_FIELDS


def person(**changes):
    return dict(id='GF-TEST', nombre='Persona de prueba', edad='30', **changes)


class ValidationTests(unittest.TestCase):
    def test_minimum_profile(self):
        profile = make_profile(person())
        self.assertEqual(profile.edad, 30)
        self.assertIsNone(profile.peso)

    def test_required_errors_identify_fields(self):
        self.assertEqual(set(validate_profile({})), {'id', 'nombre', 'edad'})

    def test_decimal_comma(self):
        self.assertEqual(make_profile(person(peso='72,5')).peso, 72.5)

    def test_non_finite_numbers_rejected(self):
        for value in ("nan", "inf", "-inf", "700", "0"):
            with self.subTest(value=value):
                self.assertIn('peso', validate_profile(person(peso=value)))

    def test_blood_pressure_relationship(self):
        self.assertIn('pad', validate_profile(person(pas='80', pad='90')))

    def test_single_optional_pressure_preserved(self):
        self.assertEqual(make_profile(person(pas='120')).pas, 120)

    def test_age_boundaries_and_integer(self):
        for age in ("-1", "121", "30.5", "", "abc"):
            data = person()
            data['edad'] = age
            self.assertIn('edad', validate_profile(data))
        data = person()
        data['edad'] = '0'
        self.assertFalse(validate_profile(data))

    def test_id_is_fixed(self):
        self.assertIn('id', validate_profile(person(), existing_id='OTHER'))

    def test_step_validation(self):
        self.assertFalse(validate_profile(person(peso='incorrecto'), only=IDENTITY_FIELDS))


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.db = Database(':memory:')
        self.records = RecordService(self.db)

    def tearDown(self):
        self.db.cerrar()

    def test_profile_round_trip_and_active_id(self):
        self.records.save_profile(person(peso='75,5', notas='Texto con acentos: corazón'))
        self.assertEqual(self.db.active_id(), 'GF-TEST')
        self.assertEqual(self.records.profile()['peso'], 75.5)
        self.assertIn('corazón', self.records.profile()['notas'])

    def test_update_keeps_studies_and_legacy_columns(self):
        self.records.save_profile(person())
        self.db.conn.execute("UPDATE pacientes SET grasa=20 WHERE id='GF-TEST'")
        self.db.guardar_medicion('GF-TEST', 72, 'FC registrada', 'Exploratorio', 'USB', 'Válida', 0.2, 0.3, '')
        data = person()
        data['nombre'] = 'Nombre editado'
        self.records.save_profile(data)
        self.assertEqual(self.records.profile()['grasa'], 20)
        self.assertEqual(len(self.db.studies('GF-TEST')), 1)

    def test_cannot_overwrite_other_code(self):
        self.db.guardar_paciente(make_profile(person()).database_values())
        with self.assertRaises(ValidationError):
            self.records.save_profile(person())

    def test_legacy_profile_can_be_activated(self):
        self.db.guardar_paciente(make_profile(person()).database_values())
        self.records.activate('GF-TEST')
        self.assertEqual(self.records.profile()['nombre'], 'Persona de prueba')

    def test_empty_consultation_is_rejected(self):
        self.records.save_profile(person())
        with self.assertRaises(ValidationError):
            self.records.save_consultation({})

    def test_consultation_round_trip(self):
        self.records.save_profile(person())
        self.records.save_consultation({'motivo': 'Seguimiento', 'notas': 'Sin cambios'})
        self.assertEqual(self.db.consultations('GF-TEST')[0]['motivo'], 'Seguimiento')

    def test_compressed_signal_round_trip(self):
        self.records.save_profile(person())
        signal = ([0, 0.005, 0.01], [1, 2, 3], [None, 0.2, 0.3])
        self.db.guardar_medicion('GF-TEST', 72, 'FC registrada', 'Exploratorio', 'USB', 'Válida', 0.2, 0.3, '', signal)
        study_id = self.db.ids_estudios('GF-TEST')[0]
        self.assertEqual(self.db.signal_detail(study_id)['y'], [1, 2, 3])
        self.assertEqual(self.db.obtener_senal(study_id), ([0, 0.005, 0.01], [None, 0.2, 0.3]))

    def test_delete_study_keeps_profile(self):
        self.records.save_profile(person())
        self.db.guardar_medicion('GF-TEST', 72, 'FC', '', 'USB', 'Pendiente', None, None, '', ([0, 1], [1, 2], [0, 0]))
        sid = self.db.ids_estudios('GF-TEST')[0]
        self.db.eliminar_estudio(sid)
        self.assertIsNone(self.db.signal_detail(sid))
        self.assertIsNotNone(self.records.profile())

    def test_malformed_signal_cannot_create_partial_row(self):
        self.records.save_profile(person())
        for signal in (([0,1],[1],[0,0]),([0,0],[1,2],[0,0]),([0,1],[1,float('nan')],[0,0])):
            with self.subTest(signal=signal):
                with self.assertRaises(ValueError):
                    self.db.guardar_medicion('GF-TEST', 72, 'FC', '', 'USB', 'Pendiente', None, None, '', signal)
        self.assertFalse(self.db.studies('GF-TEST'))

    def test_delete_profile_includes_consultations(self):
        self.records.save_profile(person())
        self.records.save_consultation({'notas': 'Nota'})
        self.assertEqual(self.db.eliminar_paciente('GF-TEST'), 1)
        self.assertFalse(self.db.consultations('GF-TEST'))
        self.assertIsNone(self.db.active_id())
        self.assertEqual(self.db.conn.execute('PRAGMA foreign_key_check').fetchall(), [])

    def test_foreign_keys_are_enabled(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.guardar_medicion('MISSING', 72, 'FC', '', 'USB', '', None, None, '')

    def test_backup_closes_destination_connection(self):
        target = sqlite3.connect(':memory:')
        try:
            with patch('geforia.persistence.database.sqlite3.connect', return_value=target):
                self.db.backup('respaldo-de-prueba.sqlite3')
            with self.assertRaises(sqlite3.ProgrammingError):
                target.execute('SELECT 1')
        finally:
            target.close()

    def test_legacy_database_migration_backup_and_idempotence(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'registros.sqlite3'
            with closing(sqlite3.connect(path)) as old, old:
                old.executescript("CREATE TABLE pacientes (id TEXT PRIMARY KEY,nombre TEXT NOT NULL,edad INTEGER NOT NULL,peso REAL,grasa REAL,medicamentos TEXT DEFAULT '',notas TEXT DEFAULT '');"
                                  "CREATE TABLE mediciones (id INTEGER PRIMARY KEY AUTOINCREMENT,paciente_id TEXT NOT NULL REFERENCES pacientes(id),fecha TEXT NOT NULL,bpm REAL,estado TEXT NOT NULL,descripcion TEXT NOT NULL,origen TEXT NOT NULL);")
                old.execute("INSERT INTO pacientes(id,nombre,edad,grasa) VALUES('OLD','Anterior',40,21)")
                old.execute("INSERT INTO mediciones(paciente_id,fecha,bpm,estado,descripcion,origen) VALUES('OLD','2026-01-01',72,'FC','','USB')")
            migrated = Database(path)
            self.assertEqual(migrated.detalle_paciente('OLD')['grasa'], 21)
            self.assertEqual(len(migrated.studies('OLD')), 1)
            migrated.cerrar()
            copies = list((Path(folder) / 'backups').glob('*.sqlite3'))
            self.assertEqual(len(copies), 1)
            with closing(sqlite3.connect(copies[0])) as backup:
                self.assertEqual(backup.execute('SELECT nombre FROM pacientes').fetchone()[0], 'Anterior')
            again = Database(path)
            again.cerrar()
            self.assertEqual(len(list((Path(folder) / 'backups').glob('*.sqlite3'))), 1)


class ProtocolTests(unittest.TestCase):
    def test_sample_units_and_nonfinite_derivative(self):
        event = parse_line('S,200,123,0.5,nan')[0]
        self.assertEqual(event[1][:2], (1.0, 0.5))
        self.assertTrue(math.isnan(event[1][2]))

    def test_beats_indices(self):
        self.assertEqual(parse_line('B,0,0,0,0,0,0,-0.4,-0.2,72'), [('indices', (-0.4, -0.2)), ('bpm', 72.0)])

    def test_result_quality_and_indices(self):
        row = ['R', '0', '72', '-.4', '0', '0', '0', '0', '0', '-.2', '0', '0', '0', '0', '1']
        self.assertEqual(parse_line(','.join(row)), [('resultado', (72.0, True, -0.4, -0.2))])

    def test_invalid_messages(self):
        for line in ('','S,a,b,c,d','S,1,1,inf,0','R,0,0','unknown','S,-1,1,0,0'):
            self.assertEqual(parse_line(line), [])

    def test_info(self):
        self.assertEqual(parse_line('# listo'), [('info', 'listo')])

    def test_fragmented_messages(self):
        buffer = LineBuffer()
        self.assertEqual(buffer.feed(b'S,200,1,'), [])
        self.assertEqual(buffer.feed(b'.5,0\n# listo\n'), ['S,200,1,.5,0\n', '# listo\n'])

    def test_oversized_frame_recovers(self):
        buffer = LineBuffer()
        self.assertEqual(buffer.feed(b'x' * 5000), [])
        self.assertEqual(buffer.feed(b'\n# listo\n'), ['# listo\n'])


class AcquisitionTests(unittest.TestCase):
    def session(self):
        s = AcquisitionSession()
        s.handle('connected', 'USB')
        s.start()
        for index in range(801):
            s.handle('muestra', (index / 20, math.sin(index), float('nan')))
        s.handle('bpm', 72.0)
        return s

    def test_start_requires_connection(self):
        with self.assertRaises(ValueError):
            AcquisitionSession().start()

    def test_complete_capture_freezes_and_retains_30_seconds(self):
        s = self.session()
        s.handle('resultado', (72.0, True, -0.4, -0.2))
        capture = s.snapshot()
        s.handle('muestra', (100, 99, 0))
        s.handle('bpm', 200)
        self.assertEqual(s.snapshot(), capture)
        self.assertEqual(capture.times[0], 0.0)
        self.assertEqual(capture.times[-1], 30.0)
        self.assertIsNone(capture.derivatives[0])
        self.assertEqual(capture.quality, 'Válida')

    def test_invalid_quality_is_preserved(self):
        s = self.session()
        s.handle('resultado', (72.0, False, None, None))
        self.assertEqual(s.snapshot().quality, 'Revisar')

    def test_partial_capture_has_pending_quality(self):
        s = self.session()
        self.assertFalse(s.can_save)
        s.handle('disconnected', None)
        self.assertTrue(s.can_save)
        self.assertEqual(s.snapshot().quality, 'Pendiente')

    def test_invalid_final_bpm_does_not_reuse_previous_value(self):
        s = self.session()
        s.handle('resultado', (None, False, None, None))
        self.assertFalse(s.can_save)

    def test_timestamp_reset_drops_old_samples(self):
        s = self.session()
        s.handle('muestra', (0.0, 1.0, 2.0))
        self.assertEqual(list(s.times), [0.0])

    def test_duplicate_save_prevented(self):
        db = Database(':memory:')
        RecordService(db).save_profile(person())
        s = self.session()
        s.handle('resultado', (72.0, True, -0.4, -0.2))
        s.save(db, 'GF-TEST')
        with self.assertRaises(ValueError):
            s.save(db, 'GF-TEST')
        self.assertEqual(len(db.studies('GF-TEST')), 1)
        db.cerrar()

    def test_new_session_clears_previous_result(self):
        s = self.session()
        s.handle('resultado', (72.0, True, -0.4, -0.2))
        s.start()
        self.assertIsNone(s.snapshot())
        self.assertTrue(s.running)


class FilterTests(unittest.TestCase):
    def test_filter_preserves_shape_and_inputs(self):
        times = [i / 200 for i in range(400)]
        values = [3 + math.sin(2 * math.pi * 1.2 * t) for t in times]
        copy = list(values)
        filtered = filtrar_ppg(times, values)
        self.assertEqual(len(filtered), 400)
        self.assertEqual(values, copy)
        self.assertTrue(all(map(math.isfinite, filtered)))

    def test_short_or_invalid_times(self):
        self.assertEqual(filtrar_ppg([0, 1], [1, 2]), [0.0, 0.0])
        self.assertEqual(filtrar_ppg([0] * 20, [1] * 20), [0.0] * 20)


if __name__ == '__main__':
    unittest.main()
