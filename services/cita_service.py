from sqlalchemy import select, text
from sqlalchemy.orm import Session, joinedload

from core.db_errors import confirmar, traduciendo
from core.errors import ErrorNegocio
from models import Cita, EstadoCita, HistorialClinico, Mascota, Veterinario
from schemas.cita import CitaIn, CompletarCitaIn


def _persona(id_, nombres, apellidos) -> dict:
    return {"id": id_, "nombre": nombres, "apellido": apellidos}


def _contexto(cita: Cita) -> dict:
    m = cita.mascota
    u = cita.veterinario.usuario
    p = m.propietario
    return {
        "mascota": {"id": m.id_mascota, "nombre": m.nombre, "especie": m.especie},
        "propietario": _persona(p.id_propietario, p.nombres, p.apellidos),
        "veterinario": _persona(cita.veterinario.id_veterinario, u.nombres, u.apellidos),
    }


def cita_a_dict(cita: Cita) -> dict:
    return {
        "id": cita.id_cita,
        "mascota_id": cita.id_mascota,
        "veterinario_id": cita.id_veterinario,
        "fecha": cita.fecha_hora,
        "motivo_consulta": cita.motivo_consulta,
        "estado": cita.estado.nombre,
        **_contexto(cita),
    }


def historial_a_dict(h: HistorialClinico) -> dict:
    return {
        "id": h.id_historial_clinico,
        "cita_id": h.id_cita,
        "fecha": h.fecha_registro,
        "diagnostico": h.diagnostico,
        "tratamiento": h.tratamiento,
        "observaciones": h.observaciones,
        **_contexto(h.cita),
    }


_CARGA_CITA = (
    joinedload(Cita.estado),
    joinedload(Cita.mascota).joinedload(Mascota.propietario),
    joinedload(Cita.veterinario).joinedload(Veterinario.usuario),
)


def _obtener(db: Session, id_cita: int) -> Cita:
    cita = db.scalars(select(Cita).where(Cita.id_cita == id_cita).options(*_CARGA_CITA)).first()
    if cita is None:
        raise ErrorNegocio(404, "Cita no encontrada")
    return cita


def _id_estado(db: Session, nombre: str) -> int:
    return db.scalar(select(EstadoCita.id_estado_cita).where(EstadoCita.nombre == nombre))


def listar(db: Session, estado: str | None, mascota_id: int | None, veterinario_id: int | None) -> list[dict]:
    consulta = select(Cita).options(*_CARGA_CITA).join(EstadoCita).order_by(Cita.fecha_hora.desc())
    if estado:
        consulta = consulta.where(EstadoCita.nombre == estado)
    if mascota_id is not None:
        consulta = consulta.where(Cita.id_mascota == mascota_id)
    if veterinario_id is not None:
        consulta = consulta.where(Cita.id_veterinario == veterinario_id)
    return [cita_a_dict(c) for c in db.scalars(consulta).unique().all()]


def crear(db: Session, datos: CitaIn) -> dict:
    if db.get(Mascota, datos.mascota_id) is None:
        raise ErrorNegocio(404, "La mascota indicada no existe")
    if db.get(Veterinario, datos.veterinario_id) is None:
        raise ErrorNegocio(404, "El veterinario indicado no existe")
    cita = Cita(
        id_mascota=datos.mascota_id,
        id_veterinario=datos.veterinario_id,
        id_estado_cita=_id_estado(db, "pendiente"),
        fecha_hora=datos.fecha,
        motivo_consulta=datos.motivo_consulta,
    )
    db.add(cita)
    confirmar(db)  # el trigger de la BD rechaza veterinarios inactivos
    return cita_a_dict(_obtener(db, cita.id_cita))


def cancelar(db: Session, id_cita: int) -> dict:
    cita = _obtener(db, id_cita)
    if cita.estado.nombre != "pendiente":
        raise ErrorNegocio(409, f"Solo se pueden cancelar citas pendientes (estado actual: {cita.estado.nombre})")
    cita.id_estado_cita = _id_estado(db, "cancelada")
    confirmar(db)
    db.expire_all()
    return cita_a_dict(_obtener(db, id_cita))


def completar(db: Session, id_cita: int, datos: CompletarCitaIn) -> dict:
    cita = _obtener(db, id_cita)
    if cita.estado.nombre != "pendiente":
        raise ErrorNegocio(409, f"Solo se pueden completar citas pendientes (estado actual: {cita.estado.nombre})")
    # La BD cambia el estado y crea el historial en una sola transacción.
    with traduciendo(db):
        id_historial = db.execute(
            text("SELECT fn_completar_cita(:id, :diagnostico, :tratamiento, :observaciones)"),
            {
                "id": id_cita,
                "diagnostico": datos.diagnostico,
                "tratamiento": datos.tratamiento,
                "observaciones": datos.observaciones,
            },
        ).scalar_one()
        db.commit()
    db.expire_all()
    return historial_a_dict(_historial(db, id_historial))


def _historial(db: Session, id_historial: int) -> HistorialClinico:
    return db.scalars(
        select(HistorialClinico)
        .where(HistorialClinico.id_historial_clinico == id_historial)
        .options(
            joinedload(HistorialClinico.cita).options(*_CARGA_CITA),
        )
    ).first()


def listar_historial(db: Session, mascota_id: int | None, veterinario_id: int | None) -> list[dict]:
    consulta = (
        select(HistorialClinico)
        .join(Cita, Cita.id_cita == HistorialClinico.id_cita)
        .options(joinedload(HistorialClinico.cita).options(*_CARGA_CITA))
        .order_by(HistorialClinico.fecha_registro.desc())
    )
    if mascota_id is not None:
        consulta = consulta.where(Cita.id_mascota == mascota_id)
    if veterinario_id is not None:
        consulta = consulta.where(Cita.id_veterinario == veterinario_id)
    return [historial_a_dict(h) for h in db.scalars(consulta).unique().all()]
