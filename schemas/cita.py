from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from schemas.comun import Entrada, PersonaResumen


class CitaIn(Entrada):
    mascota_id: int
    veterinario_id: int
    fecha: datetime
    motivo_consulta: str


class CompletarCitaIn(Entrada):
    diagnostico: str
    tratamiento: str | None = None
    observaciones: str | None = None


class MascotaDeCita(BaseModel):
    id: int
    nombre: str
    especie: str


class CitaOut(BaseModel):
    id: int
    mascota_id: int
    veterinario_id: int
    fecha: datetime
    motivo_consulta: str
    estado: Literal["pendiente", "completada", "cancelada"]
    mascota: MascotaDeCita
    propietario: PersonaResumen
    veterinario: PersonaResumen


class HistorialOut(BaseModel):
    id: int
    cita_id: int
    fecha: datetime
    diagnostico: str | None
    tratamiento: str | None
    observaciones: str | None
    mascota: MascotaDeCita
    propietario: PersonaResumen
    veterinario: PersonaResumen
