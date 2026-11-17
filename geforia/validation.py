"""Validación compartida por formularios y servicios."""
import math
from .models import Profile

REQUIRED_FIELDS = ('id', 'nombre', 'edad')
IDENTITY_FIELDS = (*REQUIRED_FIELDS, 'sexo')
HEALTH_FIELDS = ("peso", "pas", "pad", "temperatura", "antecedentes",
                 "tabaquismo", "actividad", "medicamentos")
LIMITS = {"peso": (0.1, 600, "Escribe un peso entre 0.1 y 600 kg."),
          "pas": (40, 300, "Escribe una sistólica entre 40 y 300 mmHg."),
          "pad": (20, 200, "Escribe una diastólica entre 20 y 200 mmHg."),
          "temperatura": (15, 45, "Escribe una temperatura entre 15 y 45 °C.")}


class ValidationError(ValueError):
    def __init__(self, errors: dict[str, str]):
        self.errors = errors
        super().__init__(next(iter(errors.values())))


def validate_profile(values: dict, existing_id: str | None = None,
                     only: tuple | None = None) -> dict[str, str]:
    """Rangos de captura heredados; no son umbrales diagnósticos."""
    errors = {}
    text = {k: str(v).strip() if v is not None else '' for k, v in values.items()}
    if not text.get("id"):
        errors['id'] = 'Escribe un código para el expediente.'
    elif existing_id and text["id"] != existing_id:
        errors['id'] = 'El código del expediente ya está fijado.'
    if not text.get("nombre"):
        errors['nombre'] = 'Escribe el nombre completo.'
    try:
        age = int(text.get('edad', ''))
        if not 0 <= age <= 120:
            raise ValueError
    except ValueError:
        errors['edad'] = 'Escribe una edad entera entre 0 y 120 años.'
    numbers = {}
    for field, (lo, hi, message) in LIMITS.items():
        value = text.get(field, '')
        if value:
            try:
                number = float(value.replace(',', '.'))
                if not math.isfinite(number) or not lo <= number <= hi:
                    raise ValueError
                numbers[field] = number
            except ValueError:
                errors[field] = message
    if "pas" in numbers and "pad" in numbers and numbers["pas"] <= numbers["pad"]:
        errors['pad'] = 'La diastólica debe ser menor que la sistólica.'
    return {k: v for k, v in errors.items() if only is None or k in only}


def make_profile(values: dict, existing_id: str | None = None) -> Profile:
    errors = validate_profile(values, existing_id)
    if errors:
        raise ValidationError(errors)
    clean = {key: "" if values.get(key) is None else str(values.get(key)).strip()
             for key in Profile.__dataclass_fields__}
    clean['edad'] = int(clean['edad'])
    for key in LIMITS:
        clean[key] = float(clean[key].replace(',', '.')) if clean[key] else None
    return Profile(**clean)
