from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload

from models import Propietario, TipoDocumento


def tipos_documento(db: Session) -> list[dict]:
    filas = db.scalars(select(TipoDocumento).order_by(TipoDocumento.id_tipo_documento)).all()
    return [{"id": t.id_tipo_documento, "nombre": t.nombre, "abreviacion": t.abreviacion} for t in filas]


def propietarios_con_mascotas(db: Session) -> list[dict]:
    filas = db.scalars(
        select(Propietario).options(selectinload(Propietario.mascotas)).order_by(Propietario.apellidos, Propietario.nombres)
    ).all()
    return [
        {
            "id": p.id_propietario,
            "nombre": p.nombres,
            "apellido": p.apellidos,
            "documento": p.documento,
            "mascotas": [{"id": m.id_mascota, "nombre": m.nombre, "especie": m.especie} for m in p.mascotas],
        }
        for p in filas
    ]


def veterinarios_activos(db: Session) -> list[dict]:
    filas = db.execute(
        text(
            """
            SELECT v.id_veterinario AS id, u.nombres AS nombre, u.apellidos AS apellido
            FROM veterinario v JOIN usuario u ON u.id_usuario = v.id_usuario
            WHERE u.activo
            ORDER BY u.apellidos, u.nombres
            """
        )
    ).mappings().all()
    return [dict(f) for f in filas]


def perfiles_de_veterinario(db: Session) -> list[dict]:
    filas = db.execute(
        text(
            """
            SELECT p.id_perfil AS id, p.nombre, p.descripcion
            FROM perfil p JOIN rol r ON r.id_rol = p.id_rol
            WHERE r.nombre = 'Veterinario' AND p.activo AND r.activo
            ORDER BY p.nombre
            """
        )
    ).mappings().all()
    return [dict(f) for f in filas]
