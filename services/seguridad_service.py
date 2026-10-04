"""Administración de la seguridad: roles, perfiles, módulos del menú y matriz de permisos.
Todo vive en la BD; aquí solo se validan las reglas que evitan que un administrador se bloquee
a sí mismo y se sincronizan las sesiones abiertas en Redis cuando algo cambia."""
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from core.db_errors import confirmar, traduciendo
from core.errors import ErrorNegocio
from models.seguridad import Modulo, Perfil, Permiso, Rol
from schemas.seguridad import ModuloActualizar, ModuloCrear, PerfilIn, RolIn
from services import auth_service

# El backend y el frontend dependen de estos nombres/códigos: no se renombran ni se desactivan.
ROLES_SISTEMA = {"Administrador", "Veterinario"}


def _es_modulo_sistema(codigo: str) -> bool:
    return codigo == "SEGURIDAD" or codigo.startswith("SEG_")


# ---------- utilidades ----------

def _sincronizar(db: Session, sesion: dict, ids_usuario: list[int] | None = None, todos: bool = False) -> None:
    """Cierra las sesiones de los usuarios afectados y actualiza la sesión de quien hizo el cambio."""
    if todos:
        auth_service.invalidar_todas(sesion["token"])
    elif ids_usuario:
        auth_service.invalidar_usuarios(ids_usuario, sesion["token"])
    auth_service.refrescar_sesion(db, sesion)


def _usuarios_de_perfil(db: Session, id_perfil: int) -> list[int]:
    return list(db.scalars(text("SELECT id_usuario FROM usuario_perfil WHERE id_perfil = :p"), {"p": id_perfil}))


def _usuarios_de_rol(db: Session, id_rol: int) -> list[int]:
    return list(
        db.scalars(
            text(
                "SELECT up.id_usuario FROM usuario_perfil up JOIN perfil p ON p.id_perfil = up.id_perfil"
                " WHERE p.id_rol = :r"
            ),
            {"r": id_rol},
        )
    )


def _perfiles_del_actor(db: Session, sesion: dict) -> set[int]:
    return set(
        db.scalars(
            text("SELECT id_perfil FROM usuario_perfil WHERE id_usuario = :u"),
            {"u": sesion["usuario"]["id_usuario"]},
        )
    )


def _roles_del_actor(db: Session, sesion: dict) -> set[int]:
    return set(
        db.scalars(
            text(
                "SELECT p.id_rol FROM usuario_perfil up JOIN perfil p ON p.id_perfil = up.id_perfil"
                " WHERE up.id_usuario = :u"
            ),
            {"u": sesion["usuario"]["id_usuario"]},
        )
    )


# ================= ROLES =================

def _rol_a_dict(r: Rol, total_perfiles: int) -> dict:
    return {
        "id": r.id_rol,
        "nombre": r.nombre,
        "activo": r.activo,
        "es_sistema": r.nombre in ROLES_SISTEMA,
        "total_perfiles": total_perfiles,
    }


def _obtener_rol(db: Session, id_rol: int) -> Rol:
    rol = db.get(Rol, id_rol)
    if rol is None:
        raise ErrorNegocio(404, "Rol no encontrado")
    return rol


def _rol_completo(db: Session, id_rol: int) -> dict:
    rol = _obtener_rol(db, id_rol)
    total = db.scalar(select(func.count()).select_from(Perfil).where(Perfil.id_rol == id_rol))
    return _rol_a_dict(rol, total)


def listar_roles(db: Session) -> list[dict]:
    filas = db.execute(
        select(Rol, func.count(Perfil.id_perfil)).outerjoin(Perfil, Perfil.id_rol == Rol.id_rol).group_by(Rol.id_rol).order_by(Rol.nombre)
    ).all()
    return [_rol_a_dict(r, total) for r, total in filas]


def crear_rol(db: Session, datos: RolIn) -> dict:
    rol = Rol(nombre=datos.nombre, activo=True)
    db.add(rol)
    confirmar(db)
    return _rol_completo(db, rol.id_rol)


def actualizar_rol(db: Session, sesion: dict, id_rol: int, datos: RolIn) -> dict:
    rol = _obtener_rol(db, id_rol)
    if rol.nombre in ROLES_SISTEMA and datos.nombre != rol.nombre:
        raise ErrorNegocio(409, f"El rol «{rol.nombre}» es del sistema y no se puede renombrar")
    rol.nombre = datos.nombre
    confirmar(db)
    _sincronizar(db, sesion, _usuarios_de_rol(db, id_rol))
    return _rol_completo(db, id_rol)


def cambiar_estado_rol(db: Session, sesion: dict, id_rol: int, activo: bool) -> dict:
    rol = _obtener_rol(db, id_rol)
    if not activo:
        if rol.nombre in ROLES_SISTEMA:
            raise ErrorNegocio(409, f"El rol «{rol.nombre}» es del sistema y no se puede desactivar")
        if id_rol in _roles_del_actor(db, sesion):
            raise ErrorNegocio(409, "No puedes desactivar un rol que tienes asignado")
    rol.activo = activo
    confirmar(db)
    _sincronizar(db, sesion, _usuarios_de_rol(db, id_rol))
    return _rol_completo(db, id_rol)


# ================= PERFILES =================

_SELECT_PERFILES = """
    SELECT p.id_perfil AS id, p.id_rol, r.nombre AS rol, p.nombre, p.descripcion, p.activo,
           (SELECT count(*) FROM usuario_perfil up WHERE up.id_perfil = p.id_perfil) AS total_usuarios
    FROM perfil p JOIN rol r ON r.id_rol = p.id_rol
    {filtro}
    ORDER BY r.nombre, p.nombre
"""


def _perfiles(db: Session, filtro: str = "", **params) -> list[dict]:
    consulta = _SELECT_PERFILES.replace("{filtro}", filtro)
    return [dict(f) for f in db.execute(text(consulta), params).mappings().all()]


def listar_perfiles(db: Session) -> list[dict]:
    return _perfiles(db)


def _perfil_completo(db: Session, id_perfil: int) -> dict:
    filas = _perfiles(db, "WHERE p.id_perfil = :id", id=id_perfil)
    if not filas:
        raise ErrorNegocio(404, "Perfil no encontrado")
    return filas[0]


def _obtener_perfil(db: Session, id_perfil: int) -> Perfil:
    perfil = db.get(Perfil, id_perfil)
    if perfil is None:
        raise ErrorNegocio(404, "Perfil no encontrado")
    return perfil


def crear_perfil(db: Session, datos: PerfilIn) -> dict:
    _obtener_rol(db, datos.id_rol)
    perfil = Perfil(id_rol=datos.id_rol, nombre=datos.nombre, descripcion=datos.descripcion, activo=True)
    db.add(perfil)
    confirmar(db)
    return _perfil_completo(db, perfil.id_perfil)


def actualizar_perfil(db: Session, sesion: dict, id_perfil: int, datos: PerfilIn) -> dict:
    perfil = _obtener_perfil(db, id_perfil)
    _obtener_rol(db, datos.id_rol)
    if datos.id_rol != perfil.id_rol and id_perfil in _perfiles_del_actor(db, sesion):
        raise ErrorNegocio(409, "No puedes cambiar el rol de un perfil que tienes asignado")
    perfil.id_rol = datos.id_rol
    perfil.nombre = datos.nombre
    perfil.descripcion = datos.descripcion
    confirmar(db)
    _sincronizar(db, sesion, _usuarios_de_perfil(db, id_perfil))
    return _perfil_completo(db, id_perfil)


def cambiar_estado_perfil(db: Session, sesion: dict, id_perfil: int, activo: bool) -> dict:
    perfil = _obtener_perfil(db, id_perfil)
    if not activo and id_perfil in _perfiles_del_actor(db, sesion):
        raise ErrorNegocio(409, "No puedes desactivar un perfil que tienes asignado")
    perfil.activo = activo
    confirmar(db)
    _sincronizar(db, sesion, _usuarios_de_perfil(db, id_perfil))
    return _perfil_completo(db, id_perfil)


# ================= MÓDULOS (menú) =================

def _modulo_a_dict(m: Modulo, nombre_padre: str | None) -> dict:
    return {
        "id": m.id_modulo,
        "id_modulo_padre": m.id_modulo_padre,
        "padre": nombre_padre,
        "codigo": m.codigo,
        "nombre": m.nombre,
        "descripcion": m.descripcion,
        "ruta": m.ruta,
        "icono": m.icono,
        "orden": m.orden,
        "activo": m.activo,
        "tipo": "opcion" if m.ruta else "carpeta",
        "es_sistema": _es_modulo_sistema(m.codigo),
    }


def _obtener_modulo(db: Session, id_modulo: int) -> Modulo:
    modulo = db.get(Modulo, id_modulo)
    if modulo is None:
        raise ErrorNegocio(404, "Módulo no encontrado")
    return modulo


def _modulo_completo(db: Session, id_modulo: int) -> dict:
    m = _obtener_modulo(db, id_modulo)
    padre = db.get(Modulo, m.id_modulo_padre).nombre if m.id_modulo_padre else None
    return _modulo_a_dict(m, padre)


def listar_modulos(db: Session) -> list[dict]:
    todos = db.scalars(select(Modulo)).all()
    por_id = {m.id_modulo: m for m in todos}

    def clave(m: Modulo):
        padre = por_id.get(m.id_modulo_padre)
        return (padre.orden if padre else m.orden, padre.id_modulo if padre else m.id_modulo, 0 if padre is None else 1, m.orden)

    ordenados = sorted(todos, key=clave)
    return [_modulo_a_dict(m, por_id[m.id_modulo_padre].nombre if m.id_modulo_padre else None) for m in ordenados]


def crear_modulo(db: Session, sesion: dict, datos: ModuloCrear) -> dict:
    if datos.id_modulo_padre is not None:
        _obtener_modulo(db, datos.id_modulo_padre)
    modulo = Modulo(
        id_modulo_padre=datos.id_modulo_padre,
        codigo=datos.codigo,
        nombre=datos.nombre,
        descripcion=datos.descripcion,
        ruta=datos.ruta,
        icono=datos.icono,
        orden=datos.orden,
        activo=True,
    )
    db.add(modulo)
    confirmar(db)  # los triggers de la BD validan el árbol de 2 niveles
    _sincronizar(db, sesion)
    return _modulo_completo(db, modulo.id_modulo)


def actualizar_modulo(db: Session, sesion: dict, id_modulo: int, datos: ModuloActualizar) -> dict:
    modulo = _obtener_modulo(db, id_modulo)
    if datos.id_modulo_padre == id_modulo:
        raise ErrorNegocio(422, "Un módulo no puede ser su propio padre")
    if datos.id_modulo_padre is not None:
        _obtener_modulo(db, datos.id_modulo_padre)
    if datos.ruta is None and modulo.ruta is not None:
        con_permisos = db.scalar(
            text("SELECT count(*) FROM perfil_modulo_permiso WHERE id_modulo = :m"), {"m": id_modulo}
        )
        if con_permisos:
            raise ErrorNegocio(409, "Esta opción tiene permisos asignados: quítalos antes de convertirla en carpeta")
    modulo.id_modulo_padre = datos.id_modulo_padre
    modulo.nombre = datos.nombre
    modulo.descripcion = datos.descripcion
    modulo.ruta = datos.ruta
    modulo.icono = datos.icono
    modulo.orden = datos.orden
    confirmar(db)
    _sincronizar(db, sesion, todos=True)
    return _modulo_completo(db, id_modulo)


def cambiar_estado_modulo(db: Session, sesion: dict, id_modulo: int, activo: bool) -> dict:
    modulo = _obtener_modulo(db, id_modulo)
    if not activo and _es_modulo_sistema(modulo.codigo):
        raise ErrorNegocio(409, f"«{modulo.nombre}» es un módulo del sistema y no se puede desactivar")
    modulo.activo = activo
    confirmar(db)
    _sincronizar(db, sesion, todos=True)
    return _modulo_completo(db, id_modulo)


def listar_permisos(db: Session) -> list[dict]:
    filas = db.scalars(select(Permiso).order_by(Permiso.id_permiso)).all()
    return [{"id": p.id_permiso, "nombre": p.nombre, "descripcion": p.descripcion} for p in filas]


# ================= MATRIZ PERFIL × MÓDULO × PERMISO =================

_SELECT_MATRIZ = """
    SELECT m.codigo, m.nombre, pa.nombre AS carpeta, m.activo,
           COALESCE(array_agg(pe.nombre ORDER BY pe.id_permiso) FILTER (WHERE pe.nombre IS NOT NULL), '{}') AS permisos
    FROM modulo m
    LEFT JOIN modulo pa ON pa.id_modulo = m.id_modulo_padre
    LEFT JOIN perfil_modulo_permiso pmp ON pmp.id_modulo = m.id_modulo AND pmp.id_perfil = :perfil
    LEFT JOIN permiso pe ON pe.id_permiso = pmp.id_permiso
    WHERE m.ruta IS NOT NULL
    GROUP BY m.id_modulo, pa.id_modulo
    ORDER BY COALESCE(pa.orden, m.orden), COALESCE(pa.id_modulo, m.id_modulo), m.orden
"""


def obtener_matriz(db: Session, id_perfil: int) -> dict:
    perfil = _obtener_perfil(db, id_perfil)
    filas = db.execute(text(_SELECT_MATRIZ), {"perfil": id_perfil}).mappings().all()
    return {
        "id_perfil": perfil.id_perfil,
        "perfil": perfil.nombre,
        "permisos_disponibles": [p["nombre"] for p in listar_permisos(db)],
        "modulos": [{**dict(f), "permisos": list(f["permisos"])} for f in filas],
    }


def guardar_matriz(db: Session, sesion: dict, id_perfil: int, asignaciones: dict[str, list[str]]) -> dict:
    _obtener_perfil(db, id_perfil)
    hojas = {
        codigo: (id_modulo, nombre)
        for codigo, id_modulo, nombre in db.execute(
            text("SELECT codigo, id_modulo, nombre FROM modulo WHERE ruta IS NOT NULL")
        ).all()
    }

    for codigo, permisos in asignaciones.items():
        if codigo not in hojas:
            raise ErrorNegocio(422, f"«{codigo}» no es una opción de menú válida (los permisos van en opciones, no en carpetas)")
        if permisos and "LEER" not in permisos:
            raise ErrorNegocio(
                422, f"Para dar permisos en «{hojas[codigo][1]}» también se necesita LEER; sin él la opción no aparece en el menú"
            )

    # Un administrador no puede quitarse a sí mismo el acceso a esta pantalla.
    if id_perfil in _perfiles_del_actor(db, sesion):
        necesarios = {"LEER", "ACTUALIZAR"}
        if not necesarios.issubset(set(asignaciones.get("SEG_MODULOS", []))):
            raise ErrorNegocio(
                409, "No puedes quitarle a tu propio perfil los permisos LEER y ACTUALIZAR de «Módulos y permisos»"
            )

    filas = [
        {"perfil": id_perfil, "modulo": hojas[codigo][0], "permiso": permiso}
        for codigo, permisos in asignaciones.items()
        for permiso in dict.fromkeys(permisos)
    ]
    with traduciendo(db):
        db.execute(text("DELETE FROM perfil_modulo_permiso WHERE id_perfil = :p"), {"p": id_perfil})
        if filas:
            db.execute(
                text(
                    "INSERT INTO perfil_modulo_permiso (id_perfil, id_modulo, id_permiso)"
                    " SELECT :perfil, :modulo, id_permiso FROM permiso WHERE nombre = :permiso"
                ),
                filas,
            )
        db.commit()

    _sincronizar(db, sesion, _usuarios_de_perfil(db, id_perfil))
    return obtener_matriz(db, id_perfil)
