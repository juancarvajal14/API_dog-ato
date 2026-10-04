from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from core.db_errors import confirmar
from core.errors import ErrorNegocio
from models import Propietario
from schemas.propietario import PropietarioIn

_CARGA = (selectinload(Propietario.mascotas), selectinload(Propietario.tipo_documento))


def a_dict(p: Propietario) -> dict:
    return {
        "id": p.id_propietario,
        "id_tipo_documento": p.id_tipo_documento,
        "tipo_documento": p.tipo_documento.abreviacion,
        "documento": p.documento,
        "nombre": p.nombres,
        "apellido": p.apellidos,
        "telefono": p.telefono,
        "email": p.email,
        "direccion": p.direccion,
        "mascotas": [{"id": m.id_mascota, "nombre": m.nombre, "especie": m.especie} for m in p.mascotas],
    }


def _obtener(db: Session, id_propietario: int) -> Propietario:
    p = db.scalars(
        select(Propietario).where(Propietario.id_propietario == id_propietario).options(*_CARGA)
    ).first()
    if p is None:
        raise ErrorNegocio(404, "Propietario no encontrado")
    return p


def _aplicar(p: Propietario, datos: PropietarioIn) -> None:
    p.id_tipo_documento = datos.id_tipo_documento
    p.documento = datos.documento
    p.nombres = datos.nombre
    p.apellidos = datos.apellido
    p.telefono = datos.telefono
    p.email = datos.email
    p.direccion = datos.direccion


def listar(db: Session) -> list[dict]:
    filas = db.scalars(
        select(Propietario).options(*_CARGA).order_by(Propietario.apellidos, Propietario.nombres)
    ).all()
    return [a_dict(p) for p in filas]


def obtener(db: Session, id_propietario: int) -> dict:
    return a_dict(_obtener(db, id_propietario))


def crear(db: Session, datos: PropietarioIn) -> dict:
    p = Propietario()
    _aplicar(p, datos)
    db.add(p)
    confirmar(db)
    return a_dict(_obtener(db, p.id_propietario))


def actualizar(db: Session, id_propietario: int, datos: PropietarioIn) -> dict:
    p = _obtener(db, id_propietario)
    _aplicar(p, datos)
    confirmar(db)
    db.expire_all()
    return a_dict(_obtener(db, id_propietario))
