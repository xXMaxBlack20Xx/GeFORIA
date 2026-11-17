"""Objetos de datos independientes de Tkinter y SQLite."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Profile:
    id: str
    nombre: str
    edad: int
    peso: float | None = None
    medicamentos: str = ''
    notas: str = ''
    sexo: str = ''
    pas: float | None = None
    pad: float | None = None
    antecedentes: str = ''
    tabaquismo: str = ''
    actividad: str = ''
    temperatura: float | None = None

    def database_values(self) -> tuple:
        return tuple((getattr(self, key) for key in self.__dataclass_fields__))


@dataclass(frozen=True)
class Capture:
    bpm: float
    ba: float | None
    agi: float | None
    origin: str
    quality: str
    times: tuple[float, ...]
    values: tuple[float, ...]
    derivatives: tuple[float | None, ...]

    @property
    def signal(self) -> tuple[list, list, list]:
        return (list(self.times), list(self.values), list(self.derivatives))
