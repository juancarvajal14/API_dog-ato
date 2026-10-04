"""Pruebas de la administración de seguridad (roles, perfiles, módulos y matriz de permisos).
Los datos que crean se llaman 'T9...' y se borran al terminar."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from core.database import engine
from main import app
from tests.test_negocio import ADMIN, VET, limpiar_datos_prueba


def limpiar_seguridad():
    limpiar_datos_prueba()  # borra también los usuarios 'T9...'
    with engine.begin() as c:
        c.execute(text("DELETE FROM perfil_modulo_permiso WHERE id_perfil IN (SELECT id_perfil FROM perfil WHERE nombre LIKE 'T9%')"))
        c.execute(text("DELETE FROM perfil_modulo_permiso WHERE id_modulo IN (SELECT id_modulo FROM modulo WHERE codigo LIKE 'T9\\_%')"))
        c.execute(text("DELETE FROM perfil WHERE nombre LIKE 'T9%'"))
        c.execute(text("DELETE FROM rol WHERE nombre LIKE 'T9%'"))
        c.execute(text("DELETE FROM modulo WHERE codigo LIKE 'T9\\_%' AND id_modulo_padre IS NOT NULL"))
        c.execute(text("DELETE FROM modulo WHERE codigo LIKE 'T9\\_%'"))


@pytest.fixture(scope="module")
def client():
    limpiar_seguridad()
    with TestClient(app) as c:
        yield c
    limpiar_seguridad()


def entrar(client, cuenta):
    r = client.post("/auth/login", json=cuenta)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def admin(client):
    return entrar(client, ADMIN)


def por_nombre(lista, nombre):
    return next(x for x in lista if x["nombre"] == nombre)


def test_veterinario_no_administra_seguridad(client):
    vet = entrar(client, VET)
    for ruta in ("/roles", "/perfiles", "/modulos", "/modulos/permisos", "/perfiles/1/permisos"):
        assert client.get(ruta, headers=vet).status_code == 403, ruta
    assert client.put("/perfiles/2/permisos", json={"asignaciones": {}}, headers=vet).status_code == 403


def test_no_hay_endpoints_de_eliminar(client, admin):
    for ruta in ("/roles/1", "/perfiles/1", "/modulos/1"):
        assert client.delete(ruta, headers=admin).status_code in (404, 405), ruta


# ---------- roles ----------

def test_roles(client, admin):
    r = client.post("/roles", json={"nombre": "T9 Rol"}, headers=admin)
    assert r.status_code == 201, r.text
    rol = r.json()
    assert rol["activo"] is True and rol["es_sistema"] is False and rol["total_perfiles"] == 0
    assert client.post("/roles", json={"nombre": "T9 Rol"}, headers=admin).status_code == 409

    assert client.put(f"/roles/{rol['id']}", json={"nombre": "T9 Rol editado"}, headers=admin).json()["nombre"] == "T9 Rol editado"

    roles = client.get("/roles", headers=admin).json()
    admin_rol = por_nombre(roles, "Administrador")
    assert admin_rol["es_sistema"] is True
    # roles del sistema y el propio rol del administrador están protegidos
    assert client.put(f"/roles/{admin_rol['id']}", json={"nombre": "Otro"}, headers=admin).status_code == 409
    assert client.patch(f"/roles/{admin_rol['id']}/estado", json={"activo": False}, headers=admin).status_code == 409
    vet_rol = por_nombre(roles, "Veterinario")
    assert client.patch(f"/roles/{vet_rol['id']}/estado", json={"activo": False}, headers=admin).status_code == 409

    r = client.patch(f"/roles/{rol['id']}/estado", json={"activo": False}, headers=admin)
    assert r.status_code == 200 and r.json()["activo"] is False
    assert client.patch(f"/roles/{rol['id']}/estado", json={"activo": True}, headers=admin).json()["activo"] is True
    assert client.put("/roles/99999999", json={"nombre": "x"}, headers=admin).status_code == 404


# ---------- perfiles ----------

def test_perfiles(client, admin):
    rol = por_nombre(client.get("/roles", headers=admin).json(), "T9 Rol editado")
    cuerpo = {"id_rol": rol["id"], "nombre": "T9 Perfil", "descripcion": ""}
    r = client.post("/perfiles", json=cuerpo, headers=admin)
    assert r.status_code == 201, r.text
    perfil = r.json()
    assert perfil["rol"] == "T9 Rol editado" and perfil["descripcion"] is None and perfil["total_usuarios"] == 0

    assert client.post("/perfiles", json=cuerpo, headers=admin).status_code == 409
    assert client.post("/perfiles", json={**cuerpo, "nombre": "T9 Otro", "id_rol": 99999999}, headers=admin).status_code == 404
    r = client.put(f"/perfiles/{perfil['id']}", json={**cuerpo, "descripcion": "Prueba"}, headers=admin)
    assert r.json()["descripcion"] == "Prueba"

    # el perfil del propio administrador está protegido
    propio = por_nombre(client.get("/perfiles", headers=admin).json(), "Administrador del sistema")
    assert propio["total_usuarios"] >= 1
    assert client.patch(f"/perfiles/{propio['id']}/estado", json={"activo": False}, headers=admin).status_code == 409
    otro_rol = por_nombre(client.get("/roles", headers=admin).json(), "Veterinario")["id"]
    r = client.put(f"/perfiles/{propio['id']}", json={"id_rol": otro_rol, "nombre": propio["nombre"]}, headers=admin)
    assert r.status_code == 409


# ---------- módulos ----------

def test_modulos(client, admin):
    carpeta = client.post("/modulos", json={"codigo": "T9_CARPETA", "nombre": "T9 Carpeta", "orden": 90}, headers=admin)
    assert carpeta.status_code == 201, carpeta.text
    assert carpeta.json()["tipo"] == "carpeta"
    idc = carpeta.json()["id"]

    opcion = {"codigo": "T9_OPCION", "nombre": "T9 Opción", "ruta": "/t9/opcion", "icono": "users",
              "orden": 1, "id_modulo_padre": idc}
    r = client.post("/modulos", json=opcion, headers=admin)
    assert r.status_code == 201, r.text
    assert r.json()["tipo"] == "opcion" and r.json()["padre"] == "T9 Carpeta"
    ido = r.json()["id"]

    # validaciones
    assert client.post("/modulos", json={**opcion, "codigo": "minuscula"}, headers=admin).status_code == 422
    assert client.post("/modulos", json={**opcion, "ruta": "sin-barra"}, headers=admin).status_code == 422
    assert client.post("/modulos", json=opcion, headers=admin).status_code == 409  # código repetido
    assert client.post("/modulos", json={**opcion, "codigo": "T9_OTRA"}, headers=admin).status_code == 409  # ruta repetida
    # reglas del árbol (triggers de la BD)
    r = client.post("/modulos", json={**opcion, "codigo": "T9_HIJA", "ruta": "/t9/hija", "id_modulo_padre": ido}, headers=admin)
    assert r.status_code == 409 and "carpeta" in r.json()["detail"]
    r = client.post("/modulos", json={**opcion, "codigo": "T9_SINRUTA", "ruta": None}, headers=admin)
    assert r.status_code == 409 and "ruta" in r.json()["detail"]
    assert client.put(f"/modulos/{idc}", json={"nombre": "x", "id_modulo_padre": idc}, headers=admin).status_code == 422

    # módulos del sistema (Seguridad) no se desactivan
    todos = client.get("/modulos", headers=admin).json()
    seg = next(m for m in todos if m["codigo"] == "SEG_MODULOS")
    assert seg["es_sistema"] is True
    assert client.patch(f"/modulos/{seg['id']}/estado", json={"activo": False}, headers=admin).status_code == 409

    # edición y estado
    r = client.put(f"/modulos/{ido}", json={"nombre": "T9 Opción 2", "ruta": "/t9/opcion", "icono": "users",
                                            "orden": 2, "id_modulo_padre": idc}, headers=admin)
    assert r.status_code == 200 and r.json()["nombre"] == "T9 Opción 2" and r.json()["orden"] == 2
    assert [m["codigo"] for m in todos][:2] == ["SEGURIDAD", "SEG_VETERINARIOS"]  # ordenados como el menú
    assert {p["nombre"] for p in client.get("/modulos/permisos", headers=admin).json()} == {"CREAR", "LEER", "ACTUALIZAR", "ELIMINAR"}


# ---------- matriz de permisos ----------

def test_matriz(client, admin):
    perfil = por_nombre(client.get("/perfiles", headers=admin).json(), "T9 Perfil")
    url = f"/perfiles/{perfil['id']}/permisos"

    matriz = client.get(url, headers=admin).json()
    codigos = [m["codigo"] for m in matriz["modulos"]]
    assert "SEGURIDAD" not in codigos and "CLI_CITAS" in codigos and "T9_OPCION" in codigos  # solo opciones, no carpetas
    assert all(m["permisos"] == [] for m in matriz["modulos"])
    assert matriz["permisos_disponibles"] == ["CREAR", "LEER", "ACTUALIZAR", "ELIMINAR"]

    assert client.put(url, json={"asignaciones": {"T9_OPCION": ["CREAR"]}}, headers=admin).status_code == 422  # sin LEER
    assert client.put(url, json={"asignaciones": {"T9_CARPETA": ["LEER"]}}, headers=admin).status_code == 422  # carpeta
    assert client.put(url, json={"asignaciones": {"NO_EXISTE": ["LEER"]}}, headers=admin).status_code == 422
    assert client.put(url, json={"asignaciones": {"CLI_CITAS": ["BORRAR"]}}, headers=admin).status_code == 422
    assert client.put("/perfiles/99999999/permisos", json={"asignaciones": {}}, headers=admin).status_code == 404

    r = client.put(url, json={"asignaciones": {"T9_OPCION": ["LEER", "CREAR"], "CLI_MASCOTAS": ["LEER"]}}, headers=admin)
    assert r.status_code == 200, r.text
    por_codigo = {m["codigo"]: m["permisos"] for m in r.json()["modulos"]}
    assert por_codigo["T9_OPCION"] == ["CREAR", "LEER"] and por_codigo["CLI_MASCOTAS"] == ["LEER"]
    assert por_codigo["CLI_CITAS"] == []

    # reemplazo completo: lo que no se envía se quita
    r = client.put(url, json={"asignaciones": {"CLI_MASCOTAS": ["LEER"]}}, headers=admin)
    assert {m["codigo"]: m["permisos"] for m in r.json()["modulos"]}["T9_OPCION"] == []


def test_administrador_no_se_bloquea_a_si_mismo(client, admin):
    propio = por_nombre(client.get("/perfiles", headers=admin).json(), "Administrador del sistema")["id"]
    antes = client.get(f"/perfiles/{propio}/permisos", headers=admin).json()
    sin_acceso = {m["codigo"]: m["permisos"] for m in antes["modulos"] if m["codigo"] != "SEG_MODULOS"}
    r = client.put(f"/perfiles/{propio}/permisos", json={"asignaciones": sin_acceso}, headers=admin)
    assert r.status_code == 409 and "Módulos y permisos" in r.json()["detail"]
    despues = client.get(f"/perfiles/{propio}/permisos", headers=admin).json()
    assert despues["modulos"] == antes["modulos"]  # no cambió nada


# ---------- sincronización de sesiones ----------

def test_cambios_cierran_sesiones_de_los_afectados(client, admin):
    rol_vet = por_nombre(client.get("/roles", headers=admin).json(), "Veterinario")["id"]
    perfil = client.post("/perfiles", json={"id_rol": rol_vet, "nombre": "T9 Perfil Vet"}, headers=admin).json()
    url = f"/perfiles/{perfil['id']}/permisos"
    assert client.put(url, json={"asignaciones": {"CLI_MASCOTAS": ["LEER"]}}, headers=admin).status_code == 200

    cuerpo = {"id_tipo_documento": 1, "documento": "T9200001", "nombre": "Sync", "apellido": "Vet",
              "email": "t9.sync@dogato-prueba.com", "password": "ClaveSegura1!", "id_perfil": perfil["id"]}
    assert client.post("/veterinarios", json=cuerpo, headers=admin).status_code == 201
    assert por_nombre(client.get("/perfiles", headers=admin).json(), "T9 Perfil Vet")["total_usuarios"] == 1

    cuenta = {"email": cuerpo["email"], "password": cuerpo["password"]}
    token_vet = entrar(client, cuenta)
    menu = lambda t: [h["codigo"] for c in client.get("/auth/me", headers=t).json()["menu"] for h in c["hijos"]]
    assert menu(token_vet) == ["CLI_MASCOTAS"]

    # 1) cambiar la matriz del perfil cierra la sesión del usuario afectado, pero no la de quien hizo el cambio
    assert client.put(url, json={"asignaciones": {"CLI_MASCOTAS": ["LEER"], "CLI_CITAS": ["LEER"]}}, headers=admin).status_code == 200
    assert client.get("/auth/me", headers=token_vet).status_code == 401
    assert client.get("/auth/me", headers=admin).status_code == 200
    token_vet = entrar(client, cuenta)
    assert menu(token_vet) == ["CLI_MASCOTAS", "CLI_CITAS"]

    # 2) desactivar un módulo cierra todas las sesiones y desaparece del menú
    opcion = next(m for m in client.get("/modulos", headers=admin).json() if m["codigo"] == "T9_OPCION")
    client.put(url, json={"asignaciones": {"CLI_MASCOTAS": ["LEER"], "T9_OPCION": ["LEER"]}}, headers=admin)
    token_vet = entrar(client, cuenta)
    assert "T9_OPCION" in menu(token_vet)
    assert client.patch(f"/modulos/{opcion['id']}/estado", json={"activo": False}, headers=admin).status_code == 200
    assert client.get("/auth/me", headers=token_vet).status_code == 401
    token_vet = entrar(client, cuenta)
    assert "T9_OPCION" not in menu(token_vet)

    # 3) el admin ve su propio menú actualizado sin volver a iniciar sesión
    assert client.get("/auth/me", headers=admin).status_code == 200

    # 4) desactivar el perfil deja al usuario sin módulos: no puede volver a entrar
    assert client.patch(f"/perfiles/{perfil['id']}/estado", json={"activo": False}, headers=admin).status_code == 200
    assert client.get("/auth/me", headers=token_vet).status_code == 401
    assert client.post("/auth/login", json=cuenta).status_code == 403
