# Historial de cambios del modelo de datos

> Para el estado vigente ver `CONTEXT.md`; la fuente de verdad es `db/DDL.sql` (único script SQL del repositorio).
> Este archivo reemplaza a la versión anterior, que describía una separación Cita/Historial ya superada.

## Versión 1 — DDL original (primera entrega, ya reemplazado)
Tablas `usuario` (con `rol` como texto), `veterinario` (FK por `documento`), `propietario`, `mascota`, `cita` e `historial_clinico` (1:1 con cita). Roles `veterinario`/`administrador` fijos en un `CHECK`; el menú y los permisos vivían en el frontend.

## Versión 2 — `DOG-ATO.sql` (propuesta de un compañero, escrita para Oracle / SQL Developer)
Respuesta a la corrección del profesor: menú, roles y permisos en la BD. Agregó `tipo_documento`, `rol`, `perfil`, `modulo`, `permiso`, `perfil_modulo_permiso`, `usuario_perfil`, `estado_cita`, y movió la identidad del veterinario a `usuario` (`veterinario.id_usuario`). El diseño era correcto, pero **no ejecutaba en PostgreSQL** (`NUMBER`, `VARCHAR2`, `CLOB`, `SYSTIMESTAMP`) y tenía huecos de integración.

## Versión 3 — `db/DDL.sql` (vigente; reemplaza a todas las anteriores)
Portada a PostgreSQL, validada en 17 y 18, con estas correcciones:

| Tema | Problema en la v2 | Solución |
|---|---|---|
| Motor | Sintaxis Oracle | Tipos y funciones PostgreSQL |
| Contraseña | Texto plano (`'Admin12345*'`) | `contrasena_hash` bcrypt (pgcrypto en el seed) |
| Dirección del veterinario | Se perdió al mover datos a `usuario` | `usuario.direccion` |
| `motivo_consulta` | Pasó a opcional | `NOT NULL` otra vez |
| Valores de dominio | `sexo` `'M'/'H'`, estado `PROGRAMADA` | `'macho'/'hembra'`, `pendiente/completada/cancelada` (iguales al DDL original y al frontend) |
| Convenciones | `estado 'A'/'I'` y `activo 0/1` mezclados | `activo BOOLEAN` en todo |
| Identificación de módulos | Por nombre con tildes | `modulo.codigo` único + `icono` |
| Menú | Sin validaciones (auto-padre, rutas repetidas, niveles ilimitados) | CHECK, índice único de ruta, trigger de 2 niveles |
| Carpetas | Con filas de LEER redundantes | Se muestran si el usuario ve alguna opción hija; trigger impide permisos sobre carpetas |
| Email | Único sensible a mayúsculas | Índice único sobre `lower(email)` |
| Índices | Faltaban en las FK | Creados |
| Integridad de citas | Nada impedía historial sin cita completada ni citas a veterinarios inactivos | Triggers + `fn_completar_cita` |
| Lógica de acceso | No existía en la BD | `fn_menu_usuario`, `fn_permisos_usuario`, `fn_tiene_permiso`, `v_matriz_permisos`, `fn_crear_veterinario` |
| Despliegue | Había que crear la BD a mano | El script borra y recrea `dogato`, con datos demo y cuentas de desarrollo |
| Tildes en Windows | `\connect` abre una conexión nueva y el cliente volvía a WIN1252: "Médico" se guardaba como "MÃ©dico" | `\encoding UTF8` también después de `\connect` (corregido el 2026-10-03; quien ejecutó el script antes debe volver a ejecutarlo) |

## Qué cambia para el API y el frontend
- Nombres: `id_*` en vez de `id`; `nombres/apellidos` en vez de `nombre/apellido`; `propietario.documento` + `id_tipo_documento`; `cita.fecha_hora` y `id_estado_cita` (en vez de `fecha` y `estado` texto); historial con `id_cita` y `fecha_registro`.
- El rol del usuario ya no es un campo: se obtiene de sus perfiles (`usuario_perfil` → `perfil` → `rol`).
- El menú y los permisos salen de `fn_menu_usuario` / `fn_tiene_permiso`; el frontend no define pestañas ni roles.
- Eliminar veterinarios no existe (solo activar/desactivar); el historial no se edita ni se borra.

## Archivos legados
Las versiones 1 y 2 (y el script de Oracle) ya no están en el repositorio: `db/DDL.sql` es el único script SQL y contiene la estructura, las reglas, la seguridad y los datos demo.
