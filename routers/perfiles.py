from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_algun_permiso, require_permiso
from schemas.seguridad import EstadoIn, MatrizIn, MatrizOut, PerfilIn, PerfilOut
from services import seguridad_service as servicio

router = APIRouter(prefix="/perfiles", tags=["Perfiles"])

MODULO = "SEG_PERFILES"


# La lista de perfiles también alimenta el selector de la pantalla "Módulos y permisos".
@router.get(
    "",
    response_model=list[PerfilOut],
    dependencies=[Depends(require_algun_permiso((MODULO, "LEER"), ("SEG_MODULOS", "LEER")))],
)
def listar(db: Session = Depends(get_db)):
    return servicio.listar_perfiles(db)


@router.post("", response_model=PerfilOut, status_code=201, dependencies=[Depends(require_permiso(MODULO, "CREAR"))])
def crear(datos: PerfilIn, db: Session = Depends(get_db)):
    return servicio.crear_perfil(db, datos)


@router.put("/{id_perfil}", response_model=PerfilOut)
def actualizar(id_perfil: int, datos: PerfilIn, db: Session = Depends(get_db), sesion: dict = Depends(require_permiso(MODULO, "ACTUALIZAR"))):
    return servicio.actualizar_perfil(db, sesion, id_perfil, datos)


@router.patch("/{id_perfil}/estado", response_model=PerfilOut)
def cambiar_estado(id_perfil: int, datos: EstadoIn, db: Session = Depends(get_db), sesion: dict = Depends(require_permiso(MODULO, "ACTUALIZAR"))):
    return servicio.cambiar_estado_perfil(db, sesion, id_perfil, datos.activo)


# ----- Matriz de permisos del perfil (pantalla "Módulos y permisos") -----
@router.get(
    "/{id_perfil}/permisos",
    response_model=MatrizOut,
    dependencies=[Depends(require_permiso("SEG_MODULOS", "LEER"))],
)
def obtener_permisos(id_perfil: int, db: Session = Depends(get_db)):
    return servicio.obtener_matriz(db, id_perfil)


@router.put("/{id_perfil}/permisos", response_model=MatrizOut)
def guardar_permisos(
    id_perfil: int,
    datos: MatrizIn,
    db: Session = Depends(get_db),
    sesion: dict = Depends(require_permiso("SEG_MODULOS", "ACTUALIZAR")),
):
    return servicio.guardar_matriz(db, sesion, id_perfil, datos.asignaciones)
