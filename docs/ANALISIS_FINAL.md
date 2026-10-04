# DOG-ATO · Análisis final (2026-10-04)

Revisión del proyecto completo (BD, API, frontend, documentación) con una prueba end to end real en Chrome.

## 1. Cómo se verificó
- **48 pruebas automáticas del API**, todas verdes sobre una BD recién creada: `test_bd` (16), `test_auth` (15), `test_negocio` (9), `test_seguridad` (8).
- **Recorrido end to end de 26 pasos en un navegador real** (Chrome headless contra una BD y un API aislados, sin tocar la BD de trabajo): login correcto e incorrecto, los 8 módulos cargan datos reales, crear propietario (y duplicado rechazado con mensaje claro), mascota, cita, completar → aparece en Historial con tildes, cancelar, crear y desactivar veterinario, crear perfil, asignar permisos en la matriz, crear módulo, sesión del admin válida tras cambiar la seguridad, veterinario con menú reducido y "Redis" en el 2.º login, historial sin botones de crear, recarga conserva la sesión, logout.
- `vite build` compila · `npm audit` (dependencias de producción): 0 vulnerabilidades · CORS rechaza orígenes ajenos · la BD de trabajo tiene las tildes correctas (script ya re-ejecutado).

## 2. Corregido durante el análisis
| # | Hallazgo | Corrección |
|---|---|---|
| 1 | El campo «Ruta» del formulario de módulos tenía una expresión regular inválida: el navegador la ignoraba y mostraba error en consola | Escapada correctamente |
| 2 | Al crear un perfil, el rol venía preseleccionado en **Administrador** (primero alfabético): riesgo de crear perfiles con el rol equivocado | Ahora no hay rol preseleccionado; hay que elegirlo |
| 3 | La pantalla de login mostraba las cuentas de prueba (con contraseña) también en una versión desplegada | Solo se muestran en `npm run dev` (o con `VITE_MOSTRAR_CUENTAS_DEMO=true`) |
| 4 | El script de **producción** incluía el teléfono de ejemplo del administrador | Se genera con `NULL` |

## 3. Pendiente — ordenado por prioridad

### Alta (afecta la nota o la seguridad del trabajo)
1. **Git sin commits.** El repositorio del API no tiene ni un commit y el del frontend tiene ~25 archivos modificados sin confirmar. Hacer commit y subir al remoto (así también lo tienen tus compañeros).
2. **Redis en la máquina de cada compañero + sus capturas** (rúbrica: 1.0 + 1.0). Guía: `REDIS_WSL.md`; guion: `DEMO_RUBRICA.md`.
3. **Documento `Evaluacion_BD2`** (rúbrica MR/3FN 0.5 + Scripts 0.5 y "Planteamiento"): diagrama ER (ya generado: `docs/modelo_er.png`; también pgAdmin → ERD), sección 8 (scripts) y 9 (roles/permisos), Redis en el stack, módulos nuevos, y quitar "enfermedades" del objetivo (no existe como tabla).
4. **Decisión en stand by:** usuarios que no son veterinarios (`CONTEXT.md` §7b). Sin ella la pantalla Perfiles no puede asignar perfiles a un usuario nuevo, salvo veterinarios.
5. **Ensayo con `DEMO_RUBRICA.md`** en la máquina de cada integrante antes de la entrega.

### Media (mejoras razonables)
- Sin paginación: las listas devuelven todos los registros (bien para el MVP; a futuro conviene paginar).
- Propietarios y mascotas no se pueden **editar desde la interfaz** (el API ya tiene `PUT`).
- Una cita se puede agendar en el pasado y dos citas del mismo veterinario pueden coincidir en hora.
- Si se desactiva un usuario directamente en SQL con credenciales aún en caché (hasta 10 min), el login responde "sin módulos habilitados" en vez de "cuenta inactiva" (desde la aplicación no ocurre: se invalida la caché).
- Redis hay que encenderlo a mano cada vez (`sudo service redis-server start`); `REDIS_WSL.md` explica la opción con systemd.
- No hay pruebas automáticas del frontend (el recorrido end to end se hizo con un script puntual que no está en el repositorio).
- 7 advertencias de lint (patrones `setState` dentro de efectos y similares); no son errores.
- (Hecho) Se eliminó `legacy_v1/` (API anterior) y los scripts SQL sobrantes: `db/DDL.sql` es el único.

### Baja / a tener presente
- El token de sesión se guarda en `localStorage` (mejorable con cookies `HttpOnly`); el límite de intentos es por correo, no por IP.
- El indicador "Credenciales validadas desde Redis/PostgreSQL" de la barra lateral es útil para la demostración; en producción se puede ocultar.
- El campo de búsqueda de Historial recorta su texto de ayuda en pantallas medianas.
- Los datos demo tienen citas pendientes con fechas pasadas (ago–sep 2026); es solo estético.
- Publicación real (Vercel + API + Postgres + Redis): sin hacer; ver `DESPLIEGUE.md`.

## 4. Estado frente a la rúbrica (sobre 5.0)
| Criterio | Peso | Estado |
|---|---|---|
| MR – 3FN | 0.5 | Modelo y argumentos listos; falta el diagrama en el documento |
| Scripts | 0.5 | Listo; falta actualizar la sección 8 del documento |
| Autenticación funcional que despliega el menú | 1.0 | Listo y verificado end to end |
| Redis instalado y configurado en cada máquina | 1.0 | Listo en la máquina de Juan Camilo; faltan los compañeros |
| Acceso a Redis y ≥ 3 instrucciones | 1.0 | Guion listo; cada integrante debe ejecutarlo |
| Usuario y contraseña en Redis desde la interfaz | 1.0 | Listo y verificado (PostgreSQL → Redis, bloqueo, logout) |
