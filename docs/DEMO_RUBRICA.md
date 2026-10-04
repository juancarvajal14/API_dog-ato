# Guion de demostración — Rúbrica "Fortalecimiento Bases de Datos Relacionales"

Cada integrante lo ejecuta **en su propia máquina** (la rúbrica evalúa a cada uno). Duración aproximada: 10–12 min.
Los comandos de Redis se escriben **uno por línea** (Redis ejecuta un comando por línea).

| # | Criterio | Peso | Parte del guion |
|---|---|---|---|
| 1 | MR – 3FN | 0.5 | Parte A |
| 2 | Scripts | 0.5 | Parte B |
| 3 | Autenticación funcional que despliega el menú | 1.0 | Parte C |
| 4 | Redis instalado y configurado en la máquina de cada integrante | 1.0 | Parte D |
| 5 | Acceso a Redis y ≥ 3 instrucciones | 1.0 | Parte E |
| 6 | Usuario y contraseña en Redis desde la interfaz | 1.0 | Parte F |

## 0. Preparación (antes de la clase, una sola vez por máquina)
1. **BD:** `psql -U postgres -f db/DDL.sql` (crea `dogato` con datos demo; en Windows usar la ruta completa de `psql.exe`).
2. **Redis en Ubuntu/WSL:** seguir `REDIS_WSL.md` (instalar, configurar usuario `dogato_api` + contraseña, `sudo service redis-server start`).
3. **API:** copiar `.env.example` → `.env` y completar `DATABASE_URL` (contraseña de su Postgres) y `REDIS_PASSWORD` (la misma del `redis.conf`). Luego:
   ```
   python -m venv venv
   .\venv\Scripts\python -m pip install -r requirements.txt
   .\venv\Scripts\python -m uvicorn main:app --reload
   ```
4. **Frontend:** `npm install`, copiar `.env.example` → `.env.local`, `npm run dev` → http://localhost:5173
5. **Ventanas abiertas durante la demo:** navegador (frontend), terminal **Ubuntu** (Redis), `psql`/pgAdmin (BD).
6. Comprobar: `http://localhost:8000/health` debe mostrar `{"status":"ok","postgres":"ok","redis":"ok"}`.

---

## Parte A · Modelo relacional en 3FN (0.5)
**Mostrar:** `docs/modelo_er.png` (generado desde la BD creada con `db/DDL.sql`) o, en vivo, pgAdmin → clic derecho en la BD `dogato` → **ERD For Database**. Captura del diagrama.

**Qué decir (por qué está en 3FN):**
- **1FN:** todos los campos son atómicos (nombres, apellidos, documento y tipo por separado; sin listas ni grupos repetidos).
- **2FN:** las tablas con llave compuesta (`usuario_perfil`, `perfil_modulo_permiso`) solo contienen la llave; no hay atributos que dependan de una parte de ella.
- **3FN:** no hay dependencias transitivas: los valores repetibles están en catálogos (`tipo_documento`, `estado_cita`, `rol`, `permiso`); los datos de identidad viven en `usuario` y los profesionales en `veterinario` (1:1); el propietario no repite datos en la mascota; el estado de la cita es una referencia, no un texto.
- **Seguridad en la BD (corrección del profesor):** `usuario → usuario_perfil → perfil → rol` y `perfil_modulo_permiso (perfil, módulo, permiso)`; el menú es la tabla `modulo` (árbol con `id_modulo_padre`).

> Pendiente del equipo: actualizar el diagrama en el documento `Evaluacion_BD2` (sección 7) con esta captura.

## Parte B · Scripts (0.5)
**Mostrar:** el archivo `db/DDL.sql` y que es repetible. En `psql -U postgres -d dogato`:
```
\dt
\df fn_*
\dy
SELECT tgname FROM pg_trigger WHERE NOT tgisinternal;
```
**Qué decir:** un único script crea la BD, tablas, llaves, índices, triggers, funciones, seguridad y datos demo; corre completo y se puede repetir.
(Opcional: mostrar `SELECT * FROM fn_menu_usuario(1);`)

## Parte C · Autenticación funcional que despliega el menú (1.0)
1. En el navegador, iniciar sesión como **administrador**: `admin@veterinaria.com` / `Admin12345*`.
   Debe verse el menú con **Seguridad** (Veterinarios, Roles, Perfiles, Módulos y permisos) y **Gestión clínica** (Propietarios, Mascotas, Citas, Historial). Captura.
2. Cerrar sesión e iniciar como **veterinario**: `andres.gomez@dogato.com` / `Vet12345*`.
   Solo ve **Gestión clínica**. Captura.
3. **Probar que el menú viene de la base de datos**, no del código. En `psql -d dogato`:
   ```sql
   SELECT codigo, permisos FROM fn_menu_usuario(
     (SELECT id_usuario FROM usuario WHERE email = 'andres.gomez@dogato.com'));
   ```
   Es exactamente lo que aparece en pantalla.
4. **Cambio en vivo (opcional, muy convincente):** quitarle el módulo Historial al perfil veterinario:
   ```sql
   DELETE FROM perfil_modulo_permiso
   WHERE id_perfil = (SELECT id_perfil FROM perfil WHERE nombre = 'Médico veterinario')
     AND id_modulo = (SELECT id_modulo FROM modulo WHERE codigo = 'CLI_HISTORIAL');
   ```
   Cerrar sesión y volver a entrar como veterinario → **ya no aparece Historial clínico**.
   **Restaurar** al terminar:
   ```sql
   INSERT INTO perfil_modulo_permiso
   SELECT p.id_perfil, m.id_modulo, pe.id_permiso
   FROM perfil p, modulo m, permiso pe
   WHERE p.nombre = 'Médico veterinario' AND m.codigo = 'CLI_HISTORIAL' AND pe.nombre = 'LEER';
   ```
   > Ojo: el menú y los permisos quedan guardados en la sesión (Redis), por eso hay que **volver a iniciar sesión** para ver el cambio. Hasta que se construyan las pantallas de Roles/Perfiles (Fase 6), los cambios hechos directo en SQL no cierran sesiones abiertas.
5. Mostrar que los botones también dependen de permisos: el veterinario ve "Nueva cita", pero en Historial no hay ningún botón de crear (solo lectura).

## Parte D · Redis instalado y configurado (1.0)
En la terminal **Ubuntu** (WSL). Capturas de:
```
wsl -l -v            # (en PowerShell) muestra Ubuntu, VERSION 2
redis-server --version
sudo service redis-server status
```
**Mostrar la configuración (sin revelar la contraseña):** en `redis-cli` autenticado (Parte E):
```
ACL LIST
```
Se ven los usuarios: `default` **off** (el acceso anónimo está deshabilitado) y `dogato_api` **on** con su contraseña guardada como hash.

**Qué decir:** Redis nativo en WSL2, solo escucha en `127.0.0.1`, con usuario y contraseña (ACL) y sin usuario anónimo.

## Parte E · Acceso a Redis y 3+ instrucciones (1.0) — cada integrante
Primero la prueba negativa:
```
redis-cli ping
```
→ `(error) NOAUTH Authentication required.` (sin credenciales no entra).

Luego entrar con usuario y contraseña (cambiar `TU_CLAVE`):
```
redis-cli --user dogato_api --pass TU_CLAVE --no-auth-warning
```
Dentro, un comando por línea:
```
PING
ACL WHOAMI
SET dogato:prueba "hola desde <tu nombre>" EX 60
GET dogato:prueba
TTL dogato:prueba
HSET dogato:demo integrante "<tu nombre>" sede "Poblado"
HGETALL dogato:demo
DEL dogato:prueba dogato:demo
```
Resultados esperados: `PONG`, `"dogato_api"`, `OK`, `"hola desde ..."`, un número cercano a 60, `(integer) 2`, los pares campo/valor y `(integer) 2`.
Captura de toda la sesión. Tiene que verse el **nombre de quien presenta**.

## Parte F · Usuario y contraseña en Redis desde la interfaz (1.0)
Dejar visibles lado a lado el navegador y la terminal con `redis-cli` autenticado.

**F0 · Estado inicial limpio** (en `redis-cli`):
```
EVAL "for _,k in ipairs(redis.call('keys','dogato:*')) do redis.call('del',k) end" 0
KEYS dogato:*
```
→ `(empty array)`.

**F1 · Primer login → se valida contra PostgreSQL y se guarda en Redis.**
En el navegador, iniciar sesión como `andres.gomez@dogato.com` / `Vet12345*`.
La barra lateral muestra **"Credenciales validadas desde PostgreSQL"**.
En `redis-cli`:
```
KEYS dogato:*
HGETALL dogato:cred:andres.gomez@dogato.com
```
Aparecen tres llaves: `dogato:cred:<correo>` (credenciales en caché), `dogato:sesion:<token>` y `dogato:usuario_sesiones:<id>`.
El `HGETALL` muestra correo, nombre y el **hash bcrypt** de la contraseña (nunca el texto plano).
```
TTL dogato:cred:andres.gomez@dogato.com      → ≈ 600 s (10 min)
```

**F2 · La sesión vive en Redis.** Copiar el token de la llave `dogato:sesion:<token>`:
```
GET dogato:sesion:<token>
TTL dogato:sesion:<token>                    → ≈ 28800 s (8 h)
```
Se ve el JSON con el usuario, el menú y los permisos que vinieron de la BD.

**F3 · Segundo login → se valida desde Redis.** Cerrar sesión (la llave `sesion:` desaparece: `EXISTS dogato:sesion:<token>` → `0`) y volver a iniciar sesión.
Ahora la barra dice **"Credenciales validadas desde Redis"**: la contraseña se comprobó contra el hash guardado en Redis, sin consultar Postgres.

**F4 · Credenciales incorrectas y bloqueo.** En el login, escribir mal la contraseña 5 veces. En `redis-cli`:
```
GET dogato:intentos:andres.gomez@dogato.com  → "5"
TTL dogato:intentos:andres.gomez@dogato.com  → ≈ 900 s
```
El sexto intento (aun con la clave correcta) responde "Demasiados intentos fallidos...". Limpiar al terminar:
```
DEL dogato:intentos:andres.gomez@dogato.com
```

**F5 · (Opcional, la prueba más fuerte) La autenticación depende de Redis.**
En Ubuntu: `sudo service redis-server stop`. Intentar iniciar sesión → mensaje *"El servicio de sesiones no está disponible"*.
`sudo service redis-server start` y el login vuelve a funcionar.

---

## Preguntas probables del profesor (y respuestas cortas)
- **¿Por qué no guardan la contraseña en texto plano en Redis?** Porque cualquiera con acceso a Redis la vería. Se guarda el hash bcrypt y se compara en el backend; Redis solo acelera la consulta.
- **¿Para qué sirve Redis aquí si ya está Postgres?** Es memoria: evita consultar la BD en cada login (credenciales en caché, 10 min) y en cada petición (la sesión, con menú y permisos, se lee de Redis). También cuenta los intentos fallidos.
- **¿Qué pasa si se cambian los permisos de un usuario con sesión abierta?** Sus permisos están en la sesión; al cerrar y volver a entrar (o al expirar), se recalculan desde la BD. Cuando se desactiva un veterinario desde la aplicación, el API borra sus sesiones y su caché de inmediato.
- **¿Dónde está la lógica de roles y permisos?** En la base de datos: tablas `rol`, `perfil`, `modulo`, `permiso`, `perfil_modulo_permiso` y funciones `fn_menu_usuario` / `fn_tiene_permiso`. El backend y el frontend solo consultan.
- **¿Por qué token y no JWT?** Con token opaco la sesión existe de verdad en Redis: se puede ver, caducar y cerrar. Un JWT viviría solo en el navegador.

## Lista de evidencias a capturar (por integrante)
- [ ] Diagrama ERD (Parte A, una vez para el equipo).
- [ ] `\dt`, `\df fn_*` y trigger list (Parte B).
- [ ] Menú del administrador y del veterinario (Parte C).
- [ ] `wsl -l -v`, versión de Redis, estado del servicio, `ACL LIST` (Parte D).
- [ ] `NOAUTH` sin credenciales + sesión de ≥ 3 comandos con el nombre visible (Parte E).
- [ ] Login → `KEYS dogato:*` / `HGETALL cred` / `GET sesion` / indicador PostgreSQL → Redis (Parte F).

## Si algo falla
| Síntoma | Solución |
|---|---|
| Login responde "no se pudo conectar con el servidor" | API apagado: `uvicorn main:app --reload` |
| Login responde "servicio de sesiones no disponible" | Redis apagado: `sudo service redis-server start` en Ubuntu |
| `WRONGPASS` en `redis-cli` | Usuario/clave distintos al `redis.conf`; ver `REDIS_WSL.md` |
| `/health` muestra `"redis":"caido"` | Revisar `REDIS_PASSWORD` en `.env` y que Redis esté encendido |
| Tildes dañadas ("MÃ©dico") | Volver a ejecutar el script actualizado (`\encoding` ya corregido) |
| Cuenta bloqueada por intentos | `DEL dogato:intentos:<correo>` en `redis-cli` |
