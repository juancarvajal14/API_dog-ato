from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_permiso
from schemas.mascota import MascotaIn, MascotaOut
from services import mascota_service as servicio

router = APIRouter(prefix="/mascotas", tags=["Mascotas"])

MODULO = "CLI_MASCOTAS"


@router.get("", response_model=list[MascotaOut], dependencies=[Depends(require_permiso(MODULO, "LEER"))])
def listar(propietario_id: int | None = None, db: Session = Depends(get_db)):
    return servicio.listar(db, propietario_id)


@router.get("/{id_mascota}", response_model=MascotaOut, dependencies=[Depends(require_permiso(MODULO, "LEER"))])
def obtener(id_mascota: int, db: Session = Depends(get_db)):
    return servicio.obtener(db, id_mascota)


@router.post("", response_model=MascotaOut, status_code=201, dependencies=[Depends(require_permiso(MODULO, "CREAR"))])
def crear(datos: MascotaIn, db: Session = Depends(get_db)):
    return servicio.crear(db, datos)


@router.put("/{id_mascota}", response_model=MascotaOut, dependencies=[Depends(require_permiso(MODULO, "ACTUALIZAR"))])
def actualizar(id_mascota: int, datos: MascotaIn, db: Session = Depends(get_db)):
    return servicio.actualizar(db, id_mascota, datos)
