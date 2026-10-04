from sqlalchemy import text
from sqlalchemy.orm import Session

from core.db_errors import confirmar, traduciendo
from core.errors import ErrorNegocio
from core.security import hashear_contrasena
from models import Usuario, Veterinario
from schemas.veterinario import VeterinarioIn
from services import auth_service

_SELECT = """
    SELECT v.id_veterinario AS id, v.id_usuario, u.id_tipo_documento, td.abreviacion AS tipo_documento,
           u.documento, u.nombres AS nombre, u.apellidos AS apellido, u.telefono, u.email, u.direccion,
           v.especialidad, v.registro_profesional, u.activo,
           COALESCE(array_agg(DISTINCT r.nombre) FILTER (WHERE r.nombre IS NOT NULL), '{}') AS roles,
           COALESCE(array_agg(DISTINCT p.nombre) FILTER (WHERE p.nombre IS NOT NULL), '{}') AS perfiles
    FROM veterinario v
    JOIN usuario u ON u.id_usuario = v.id_usuario
    JOIN tipo_documento td ON td.id_tipo_documento = u.id_tipo_documento
    LEFT JOIN usuario_perfil up ON up.id_usuario = u.id_usuario
    LEFT JOIN perfil p ON p.id_perfil = up.id_perfil
    LEFT JOIN rol r ON r.id_rol = p.id_rol
    {filtro}
    GROUP BY v.id_veterinario, u.id_usuario, td.id_tipo_documento
    ORDER BY u.apellidos, u.nombres
"""


def _a_dict(fila) -> dict:
    datos = dict(fila)
    roles = datos.pop("roles")
    datos["rol"] = "administrador" if "Administrador" in roles else "veterinario"
    datos["perfiles"] = list(datos["perfiles"])
    return datos


def listar(db: Session) -> list[dict]:
    return [_a_dict(f) for f in db.execute(text(_SELECT.replace("{filtro}", ""))).mappings().all()]


def obtener(db: Session, id_veterinario: int) -> dict:
    fila = db.execute(
        text(_SELECT.replace("{filtro}", "WHERE v.id_veterinario = :id")), {"id": id_veterinario}
    ).mappings().first()
    if fila is None:
        raise ErrorNegocio(404, "Veterinario no encontrado")
    return _a_dict(fila)


def crear(db: Session, datos: VeterinarioIn) -> dict:
    # fn_crear_veterinario crea usuario + perfil + datos profesionales de forma atómica
    # y valida que el perfil pertenezca al rol Veterinario.
    with traduciendo(db):
        id_veterinario = db.execute(
            text(
                "SELECT fn_crear_veterinario(:tipo, :documento, :nombres, :apellidos, :email, :telefono,"
                " :direccion, :hash, :especialidad, :registro, :perfil)"
            ),
            {
                "tipo": datos.id_tipo_documento,
                "documento": datos.documento,
                "nombres": datos.nombre,
                "apellidos": datos.apellido,
                "email": datos.email,
                "telefono": datos.telefono,
                "direccion": datos.direccion,
                "hash": hashear_contrasena(datos.password),
                "especialidad": datos.especialidad,
                "registro": datos.registro_profesional,
                "perfil": datos.id_perfil,
            },
        ).scalar_one()
        db.commit()
    return obtener(db, id_veterinario)


def cambiar_estado(db: Session, id_veterinario: int, activo: bool, id_usuario_actor: int) -> dict:
    veterinario = db.get(Veterinario, id_veterinario)
    if veterinario is None:
        raise ErrorNegocio(404, "Veterinario no encontrado")
    if veterinario.id_usuario == id_usuario_actor:
        raise ErrorNegocio(409, "No puedes cambiar el estado de tu propia cuenta")
    usuario = db.get(Usuario, veterinario.id_usuario)
    usuario.activo = activo
    confirmar(db)
    # Cierra sus sesiones y descarta la caché de credenciales en Redis para que el cambio rija ya.
    auth_service.invalidar_usuario(usuario.id_usuario, usuario.email)
    return obtener(db, id_veterinario)
