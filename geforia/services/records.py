"""Casos de uso del expediente y el seguimiento."""
from uuid import uuid4
from ..validation import make_profile, ValidationError


class RecordService:
    def __init__(self, database):
        self.database = database
        self.active_id = database.active_id()

    def new_code(self) -> str:
        while True:
            code = 'GF-' + uuid4().hex[:8].upper()
            if not self.database.paciente(code):
                return code

    def profile(self) -> dict | None:
        return self.database.detalle_paciente(self.active_id) if self.active_id else None

    def save_profile(self, values: dict):
        profile = make_profile(values, self.active_id)
        # Un código heredado nunca se sobreescribe accidentalmente al dar de alta.
        if not self.active_id and self.database.paciente(profile.id):
            raise ValidationError({'id': 'Ese código ya existe. Selecciona su expediente o usa otro código.'})
        self.database.guardar_paciente(profile.database_values(), activate=True)
        self.active_id = profile.id
        return profile

    def activate(self, pid: str):
        if self.active_id:
            raise ValueError('Ya existe un expediente activo en esta sesión.')
        self.database.activate_profile(pid)
        self.active_id = pid

    def save_consultation(self, values: dict):
        if not self.active_id:
            raise ValueError('Primero guarda el expediente personal.')
        clean = {key: str(values.get(key, "")).strip() for key in
                 ("motivo", "presion", "medicacion", "notas")}
        if not any(clean.values()):
            raise ValidationError({'motivo': 'Escribe al menos un dato de la consulta.'})
        self.database.save_consultation(self.active_id, clean)
