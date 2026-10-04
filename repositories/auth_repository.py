from sqlalchemy import text
from sqlalchemy.orm import Session


def buscar_usuario_por_email(db: Session, email: str) -> dict | None:
    fila = db.execute(
        text(
            """
            SELECT id_usuario, nombres, apellidos, email, contrasena_hash, activo
            FROM usuario
            WHERE lower(email) = lower(:email)
            """
        ),
        {"email": email},
    ).mappings().first()
    return dict(fila) if fila else None


def menu_usuario(db: Session, id_usuario: int) -> list[dict]:
    filas = db.execute(
        text("SELECT * FROM fn_menu_usuario(:id)"),
        {"id": id_usuario},
    ).mappings().all()
    return [dict(f) for f in filas]


def permisos_por_modulo(db: Session, id_usuario: int) -> dict[str, list[str]]:
    filas = db.execute(
        text(
            """
            SELECT m.codigo, array_agg(fp.permiso ORDER BY fp.permiso) AS permisos
            FROM fn_permisos_usuario(:id) fp
            JOIN modulo m ON m.id_modulo = fp.id_modulo
            GROUP BY m.codigo
            """
        ),
        {"id": id_usuario},
    ).all()
    return {codigo: list(permisos) for codigo, permisos in filas}


def roles_y_perfiles(db: Session, id_usuario: int) -> tuple[list[str], list[str]]:
    filas = db.execute(
        text(
            """
            SELECT r.nombre AS rol, p.nombre AS perfil
            FROM usuario_perfil up
            JOIN perfil p ON p.id_perfil = up.id_perfil AND p.activo
            JOIN rol r ON r.id_rol = p.id_rol AND r.activo
            WHERE up.id_usuario = :id
            ORDER BY r.nombre, p.nombre
            """
        ),
        {"id": id_usuario},
    ).all()
    roles = sorted({r for r, _ in filas})
    perfiles = [p for _, p in filas]
    return roles, perfiles
