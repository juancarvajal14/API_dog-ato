from contextlib import contextmanager

import psycopg.errors as pg
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from core.errors import ErrorNegocio

_DUPLICADOS = {
    "uq_propietario_documento": "Ya existe un propietario con ese tipo y número de documento",
    "uq_usuario_documento": "Ya existe un usuario con ese tipo y número de documento",
    "uq_usuario_email": "Ya existe un usuario con ese correo",
    "uq_veterinario_registro": "Ya existe un veterinario con ese registro profesional",
    "uq_rol_nombre": "Ya existe un rol con ese nombre",
    "uq_perfil_nombre": "Ya existe un perfil con ese nombre",
    "uq_modulo_codigo": "Ya existe un módulo con ese código",
    "uq_modulo_ruta": "Ya existe un módulo con esa ruta",
}


def traducir(error: DBAPIError) -> ErrorNegocio | None:
    """Convierte un error de la BD (restricciones y triggers) en un mensaje entendible. None si no se reconoce."""
    original = error.orig
    if isinstance(original, pg.UniqueViolation):
        constraint = original.diag.constraint_name
        return ErrorNegocio(409, _DUPLICADOS.get(constraint, "El registro ya existe"))
    if isinstance(original, pg.ForeignKeyViolation):
        return ErrorNegocio(400, "Hace referencia a un registro que no existe")
    if isinstance(original, pg.CheckViolation):
        return ErrorNegocio(422, "Alguno de los datos no cumple las reglas del sistema")
    if isinstance(original, pg.RaiseException):  # reglas escritas en triggers/funciones de la BD
        return ErrorNegocio(409, original.diag.message_primary or "Operación no permitida")
    return None


@contextmanager
def traduciendo(db: Session):
    """Dentro del bloque, los errores de la BD se revierten y se convierten en ErrorNegocio."""
    try:
        yield
    except DBAPIError as error:
        db.rollback()
        traducido = traducir(error)
        if traducido is None:
            raise
        raise traducido from error


def confirmar(db: Session) -> None:
    with traduciendo(db):
        db.commit()
