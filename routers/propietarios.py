from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_permiso
from schemas.propietario import PropietarioIn, PropietarioOut
from services import propietario_service as servicio

router = APIRouter(prefix="/propietarios", tags=["Propietarios"])

MODULO = "CLI_PROPIETARIOS"


@router.get("", response_model=list[PropietarioOut], dependencies=[Depends(require_permiso(MODULO, "LEER"))])
def listar(db: Session = Depends(get_db)):
    return servicio.listar(db)


@router.get("/{id_propietario}", response_model=PropietarioOut, dependencies=[Depends(require_permiso(MODULO, "LEER"))])
def obtener(id_propietario: int, db: Session = Depends(get_db)):
    return servicio.obtener(db, id_propietario)


@router.post("", response_model=PropietarioOut, status_code=201, dependencies=[Depends(require_permiso(MODULO, "CREAR"))])
def crear(datos: PropietarioIn, db: Session = Depends(get_db)):
    return servicio.crear(db, datos)


@router.put("/{id_propietario}", response_model=PropietarioOut, dependencies=[Depends(require_permiso(MODULO, "ACTUALIZAR"))])
def actualizar(id_propietario: int, datos: PropietarioIn, db: Session = Depends(get_db)):
    return servicio.actualizar(db, id_propietario, datos)
