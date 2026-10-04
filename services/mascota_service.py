from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from core.db_errors import confirmar
from core.errors import ErrorNegocio
from models import Mascota, Propietario
from schemas.mascota import MascotaIn


def a_dict(m: Mascota) -> dict:
    p = m.propietario
    return {
        "id": m.id_mascota,
        "nombre": m.nombre,
        "especie": m.especie,
        "raza": m.raza,
        "sexo": m.sexo,
        "fecha_nacimiento": m.fecha_nacimiento,
        "propietario_id": m.id_propietario,
        "propietario": {"id": p.id_propietario, "nombre": p.nombres, "apellido": p.apellidos, "telefono": p.telefono},
    }


def _consulta():
    return select(Mascota).options(joinedload(Mascota.propietario))


def _obtener(db: Session, id_mascota: int) -> Mascota:
    m = db.scalars(_consulta().where(Mascota.id_mascota == id_mascota)).first()
    if m is None:
        raise ErrorNegocio(404, "Mascota no encontrada")
    return m


def _aplicar(db: Session, m: Mascota, datos: MascotaIn) -> None:
    if db.get(Propietario, datos.propietario_id) is None:
        raise ErrorNegocio(404, "El propietario indicado no existe")
    m.id_propietario = datos.propietario_id
    m.nombre = datos.nombre
    m.especie = datos.especie
    m.raza = datos.raza
    m.sexo = datos.sexo
    m.fecha_nacimiento = datos.fecha_nacimiento


def listar(db: Session, propietario_id: int | None = None) -> list[dict]:
    consulta = _consulta().order_by(Mascota.nombre)
    if propietario_id is not None:
        consulta = consulta.where(Mascota.id_propietario == propietario_id)
    return [a_dict(m) for m in db.scalars(consulta).unique().all()]


def obtener(db: Session, id_mascota: int) -> dict:
    return a_dict(_obtener(db, id_mascota))


def crear(db: Session, datos: MascotaIn) -> dict:
    m = Mascota()
    _aplicar(db, m, datos)
    db.add(m)
    confirmar(db)
    return a_dict(_obtener(db, m.id_mascota))


def actualizar(db: Session, id_mascota: int, datos: MascotaIn) -> dict:
    m = _obtener(db, id_mascota)
    _aplicar(db, m, datos)
    confirmar(db)
    db.expire_all()
    return a_dict(_obtener(db, id_mascota))
