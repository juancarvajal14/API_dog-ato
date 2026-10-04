from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_permiso
from schemas.cita import CitaIn, CitaOut, CompletarCitaIn, HistorialOut
from services import cita_service as servicio

router = APIRouter(prefix="/citas", tags=["Citas"])

MODULO = "CLI_CITAS"


@router.get("", response_model=list[CitaOut], dependencies=[Depends(require_permiso(MODULO, "LEER"))])
def listar(
    estado: Literal["pendiente", "completada", "cancelada"] | None = None,
    mascota_id: int | None = None,
    veterinario_id: int | None = None,
    db: Session = Depends(get_db),
):
    return servicio.listar(db, estado, mascota_id, veterinario_id)


@router.post("", response_model=CitaOut, status_code=201, dependencies=[Depends(require_permiso(MODULO, "CREAR"))])
def crear(datos: CitaIn, db: Session = Depends(get_db)):
    return servicio.crear(db, datos)


@router.post("/{id_cita}/cancelar", response_model=CitaOut, dependencies=[Depends(require_permiso(MODULO, "ACTUALIZAR"))])
def cancelar(id_cita: int, db: Session = Depends(get_db)):
    return servicio.cancelar(db, id_cita)


# Completar = ACTUALIZAR sobre Citas; devuelve el registro de historial clínico generado.
@router.post(
    "/{id_cita}/completar",
    response_model=HistorialOut,
    status_code=201,
    dependencies=[Depends(require_permiso(MODULO, "ACTUALIZAR"))],
)
def completar(id_cita: int, datos: CompletarCitaIn, db: Session = Depends(get_db)):
    return servicio.completar(db, id_cita, datos)
