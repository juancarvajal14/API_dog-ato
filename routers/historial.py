from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_permiso
from schemas.cita import HistorialOut
from services import cita_service as servicio

router = APIRouter(prefix="/historial", tags=["Historial clínico"])


# Solo lectura: el historial se crea únicamente al completar una cita (POST /citas/{id}/completar).
@router.get("", response_model=list[HistorialOut], dependencies=[Depends(require_permiso("CLI_HISTORIAL", "LEER"))])
def listar(mascota_id: int | None = None, veterinario_id: int | None = None, db: Session = Depends(get_db)):
    return servicio.listar_historial(db, mascota_id, veterinario_id)
