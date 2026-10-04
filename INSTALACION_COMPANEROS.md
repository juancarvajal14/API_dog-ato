# DOG-ATO · Guía de instalación paso a paso (réplica completa del proyecto)

Con esta guía cada integrante deja en **su propio computador** una réplica 100 % funcional de DOG-ATO. Lo único que cambia entre
integrantes son **sus propias claves** de PostgreSQL y de Redis; todo lo demás (base de datos, código, datos de prueba) es idéntico.

> **¿Prefieres que lo haga una IA?** Salta a la [sección 12](#12-instrucciones-para-un-asistente-de-ia): tiene un prompt listo y un
> protocolo para que cualquier asistente (ChatGPT, Claude, Gemini, Copilot…) te guíe o ejecute los pasos contigo.

---

## 0. Qué vas a construir

```
Navegador ──► Frontend (React, puerto 5173) ──► API (FastAPI, puerto 8000) ──┬──► PostgreSQL (puerto 5432)  base "dogato"
                                                                              └──► Redis (puerto 6379)  en WSL/Ubuntu
```

| Pieza | Para qué sirve | Dónde vive |
|---|---|---|
| **PostgreSQL** | Guarda TODO: datos de la clínica **y** el menú, roles, perfiles y permisos | Instalado en Windows |
| **Redis** | Solo para el login: guarda la sesión, cuenta intentos fallidos y cachea credenciales | Dentro de **Ubuntu (WSL)** |
| **API** (`API_dog-ato`) | Lógica del sistema; habla con Postgres y Redis | Carpeta de tu PC |
| **Frontend** (`APP_dog-ato`) | La pantalla que ves en el navegador | Carpeta de tu PC |

Al terminar tendrás **dos carpetas hermanas**, por ejemplo:
```
C:\Users\TU_USUARIO\Desktop\API_dog-ato
C:\Users\TU_USUARIO\Desktop\APP_dog-ato
```

### Las únicas 4 claves que cambian en cada PC
| Clave | Quién la define | Dónde se escribe |
|---|---|---|
| Contraseña de **PostgreSQL** (usuario `postgres`) | La pusiste al instalar Postgres | `API_dog-ato\.env` → `DATABASE_URL` |
| Contraseña de **Redis** (usuario `dogato_api`) | La inventas tú en el paso 6 | `redis.conf` (en Ubuntu) **y** `API_dog-ato\.env` → `REDIS_PASSWORD` |
| Contraseña de **Ubuntu** (usuario de Linux) | La creas al abrir Ubuntu por 1.ª vez | Solo la pide `sudo` |

> ⚠️ **Nunca** subas a GitHub el archivo `.env` ni compartas tus claves por chat. El proyecto ya tiene `.env` en `.gitignore`.

---

## 1. Requisitos previos (instalar una sola vez)

Abre **PowerShell** y verifica cada uno. Si un comando falla ("no se reconoce"), instálalo con el enlace.

| # | Requisito | Verificar con | Versión mínima | Instalar |
|---|---|---|---|---|
| 1.1 | Git | `git --version` | cualquiera | https://git-scm.com/download/win |
| 1.2 | Python | `python --version` | 3.12 (probado con 3.14) | https://www.python.org/downloads/ → marca **"Add python.exe to PATH"** |
| 1.3 | Node.js | `node --version` | 20 (probado con 22) | https://nodejs.org (versión LTS) |
| 1.4 | PostgreSQL | abre el programa **pgAdmin** o ejecuta el paso 3.1 | **13 o superior** (probado con 17 y 18) | https://www.postgresql.org/download/windows/ |
| 1.5 | WSL 2 con Ubuntu | `wsl -l -v` | Ubuntu en VERSION 2 | paso 5 |
| 1.6 | Editor (opcional) | — | — | VS Code |

**Al instalar PostgreSQL** te pedirá una contraseña para el superusuario `postgres`: **anótala**, la usarás en los pasos 3 y 7.
Deja el puerto por defecto **5432**.

---

## 2. Descargar el código (dos repositorios)

2.1 Elige una carpeta (ejemplo: el Escritorio) y ábrela en PowerShell:
```powershell
cd $HOME\Desktop
```
2.2 Clona los dos repositorios (necesitas acceso al repositorio de GitHub del equipo):
```powershell
git clone https://github.com/juancarvajal14/API_dog-ato.git
git clone https://github.com/juancarvajal14/APP_dog-ato.git
```
2.3 Comprueba que existen ambas carpetas:
```powershell
dir
```
Más adelante, para recibir cambios del equipo: `git pull` dentro de cada carpeta.

---

## 3. Crear la base de datos (un solo archivo, una sola ejecución)

El archivo **`API_dog-ato\db\DDL.sql`** es el **único script SQL** del proyecto. En una sola ejecución:
crea la base `dogato`, las 14 tablas, las funciones y triggers, el menú, roles, perfiles y permisos, las cuentas de prueba y datos demo.

3.1 Localiza `psql.exe` (el cliente de PostgreSQL). Normalmente está en:
```
C:\Program Files\PostgreSQL\<VERSION>\bin\psql.exe        (ejemplo: ...\PostgreSQL\18\bin\psql.exe)
```
Comprueba tu versión y ruta real:
```powershell
dir "C:\Program Files\PostgreSQL"
```
3.2 Ejecuta el script (cambia `18` por TU versión). Te pedirá la contraseña de `postgres` (al escribirla **no se ve nada**, es normal):
```powershell
cd $HOME\Desktop\API_dog-ato
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -f db\DDL.sql
```
3.3 **Resultado esperado:** al final aparece `COMMIT`, sin líneas que digan `ERROR`.

3.4 Verifica que quedó bien:
```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -d dogato -c "select email, activo from usuario order by 1;"
```
Deben salir 4 usuarios: `admin@veterinaria.com`, `andres.gomez@dogato.com`, `laura.martinez@dogato.com`, `diego.salazar@dogato.com` (este último inactivo).

> ⚠️ **El script BORRA y recrea la base `dogato` cada vez que se ejecuta** (así todos quedan idénticos). Si en tu PC ya existe una base
> llamada `dogato` con datos tuyos, se perderán. Es lo esperado en desarrollo.
>
> ℹ️ Debe ejecutarse con **psql** (no con la ventana de consultas de pgAdmin, que no entiende los comandos `\connect`).
> Si falla con "psql no se reconoce", usa la ruta completa como en 3.2. Si dice `password authentication failed`, la contraseña es incorrecta.

---

## 4. Cuentas de prueba que crea el script

| Perfil | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@veterinaria.com` | `Admin12345*` |
| Veterinario | `andres.gomez@dogato.com` | `Vet12345*` |
| Veterinario | `laura.martinez@dogato.com` | `Vet12345*` |
| Veterinario (inactivo) | `diego.salazar@dogato.com` | `Vet12345*` |

---

## 5. Instalar Ubuntu en WSL (solo si aún no lo tienes)

Redis corre dentro de Linux. WSL te da un Linux dentro de Windows.

5.1 Comprueba si ya tienes Ubuntu:
```powershell
wsl -l -v
```
Si aparece `Ubuntu` con VERSION `2`, **salta al paso 6**. Si solo aparece `docker-desktop` o nada, continúa.

5.2 Abre **PowerShell como administrador** (clic derecho → *Ejecutar como administrador*) e instala:
```powershell
wsl --install -d Ubuntu
```
5.3 **Reinicia el PC** si te lo pide.
5.4 Abre la aplicación **Ubuntu** desde el menú Inicio. La primera vez te pedirá crear un **usuario y contraseña de Linux**: anótalos
(la contraseña la pedirá cada `sudo`, al escribirla tampoco se ve nada).
5.5 Confirma: `wsl -l -v` debe mostrar `Ubuntu ... 2`.

> A partir de aquí, los pasos marcados **(Ubuntu)** se ejecutan en la ventana negra de **Ubuntu**, no en PowerShell. El prompt de Ubuntu
> se parece a `usuario@PC:~$`.

---

## 6. Instalar y configurar Redis (Ubuntu)

6.1 **(Ubuntu)** Actualiza e instala Redis:
```bash
sudo apt update
sudo apt install -y redis-server
redis-server --version
```
Debe mostrar una versión (por ejemplo `Redis server v=7.0.15`).

6.2 **Inventa tu contraseña de Redis** (será distinta a la de tus compañeros). Usa solo letras, números, `_` y `-`, **sin espacios** ni
símbolos raros, mínimo 12 caracteres. Ejemplo: `MiRedis_2026_Seguro`. Anótala: la usarás otra vez en el paso 7.

6.3 **(Ubuntu)** Configura el usuario `dogato_api` con tu contraseña y desactiva el acceso anónimo.
**Cambia `TU_CLAVE_REDIS` por tu contraseña antes de pegar:**
```bash
sudo tee -a /etc/redis/redis.conf > /dev/null <<'EOF'

# --- DOG-ATO ---
bind 127.0.0.1 -::1
protected-mode yes
user default off
user dogato_api on >TU_CLAVE_REDIS ~* &* +@all
EOF
```
Qué hace: deja Redis escuchando solo en tu PC (`bind`), **apaga** el usuario anónimo (`user default off`) y crea el usuario
`dogato_api` con su contraseña (`>` precede a la contraseña) y permisos completos.

> Si en `/etc/redis/redis.conf` ya existía una línea `user default ...` o `requirepass ...`, comenta esa línea con `#`
> (`sudo nano /etc/redis/redis.conf`; guardar: `Ctrl+O`, Enter; salir: `Ctrl+X`), porque Redis no arranca con la configuración duplicada.

6.4 **(Ubuntu)** Enciende Redis:
```bash
sudo service redis-server start
sudo service redis-server status
```
Debe decir que está corriendo (`active (running)` o `redis-server is running`). Para apagarlo: `sudo service redis-server stop`.

6.5 **(Ubuntu)** Prueba que funciona. Primero **sin** credenciales (debe rechazarte):
```bash
redis-cli ping
```
Resultado esperado: `(error) NOAUTH Authentication required.` → significa que está protegido. Ahora **con** tu usuario y contraseña
(cambia `TU_CLAVE_REDIS`):
```bash
redis-cli --user dogato_api --pass TU_CLAVE_REDIS --no-auth-warning
```
Dentro del prompt `127.0.0.1:6379>` escribe **un comando por línea**:
```
PING
ACL WHOAMI
EXIT
```
Esperado: `PONG`, `"dogato_api"`. Si sale `WRONGPASS`, la contraseña no coincide con la del `redis.conf` (revisa 6.3 y ejecuta `sudo service redis-server restart`).

6.6 **Desde Windows**, comprueba que PowerShell llega a Redis (WSL2 expone el puerto en `localhost`):
```powershell
Test-NetConnection localhost -Port 6379
```
Debe mostrar `TcpTestSucceeded : True`.

> 🔁 **Cada vez que enciendas el PC**, Redis no arranca solo: abre Ubuntu y ejecuta `sudo service redis-server start`
> (o `wsl -d Ubuntu -u root service redis-server start` desde PowerShell).

---

## 7. Configurar y arrancar la API

### 7.1 ¿Qué es el `venv`? (entorno virtual de Python)
Es una carpeta (`venv\`) que contiene **una copia aislada de Python con las librerías del proyecto** (FastAPI, SQLAlchemy, redis, bcrypt…).
Sirve para no mezclar las librerías de este proyecto con las de otros en tu PC. **No se sube a GitHub**: cada persona crea el suyo con
el comando 7.3. Mientras no exista `venv\`, el API no tiene sus librerías.

### 7.2 ¿Qué es el archivo `.env`? (variables de entorno)
Es un archivo de texto con **tus claves y direcciones de conexión**. El código las lee al arrancar. Como contiene contraseñas, **no se
sube a GitHub** (está en `.gitignore`). En el repositorio solo existe la plantilla `.env.example`; tú copias esa plantilla a `.env` y
pones TUS valores. **Por eso cada integrante tiene un `.env` diferente.**

### 7.3 Crear el entorno virtual e instalar librerías
```powershell
cd $HOME\Desktop\API_dog-ato
python -m venv venv
.\venv\Scripts\python -m pip install --upgrade pip
.\venv\Scripts\python -m pip install -r requirements-dev.txt
```
- Línea 2 crea la carpeta `venv`. Línea 4 instala las librerías de `requirements.txt` (producción) más `pytest` y `httpx` (pruebas).
- Verifica: `.\venv\Scripts\python -m pip list` debe incluir `fastapi`, `redis`, `bcrypt`, `psycopg`, `SQLAlchemy`.
- *(Opcional)* "Activar" el venv para escribir `python` en vez de `.\venv\Scripts\python`: `.\venv\Scripts\Activate.ps1`. Si PowerShell
  responde que la ejecución de scripts está deshabilitada, ejecuta antes `Set-ExecutionPolicy -Scope Process Bypass` o simplemente usa
  siempre `.\venv\Scripts\python ...` como en esta guía (no necesita activarse).

### 7.4 Crear TU archivo `.env`
```powershell
copy .env.example .env
notepad .env
```
Se abre el Bloc de notas con esta plantilla. **Edita solo estas líneas** (sin espacios alrededor del `=`, sin comillas):

```ini
DATABASE_URL=postgresql+psycopg://postgres:TU_CLAVE_POSTGRES@localhost:5432/dogato
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_USER=dogato_api
REDIS_PASSWORD=TU_CLAVE_REDIS
```

| Variable | Qué poner | Ejemplo |
|---|---|---|
| `DATABASE_URL` | Cambia `TU_CLAVE_POSTGRES` por la contraseña del usuario `postgres` de **tu** Postgres (paso 1) | `postgresql+psycopg://postgres:Abc123@localhost:5432/dogato` |
| `REDIS_HOST` / `REDIS_PORT` | Déjalos como están | `localhost` / `6379` |
| `REDIS_USER` | Déjalo como está (el usuario que creaste en 6.3) | `dogato_api` |
| `REDIS_PASSWORD` | **La misma** contraseña que pusiste en `redis.conf` (6.3) | `MiRedis_2026_Seguro` |

> ⚠️ **Si tu contraseña de Postgres tiene símbolos** (`@ : / # ? % & espacio`), debes "codificarla" en la URL o la conexión fallará.
> Ejecuta esto, pega tu contraseña real y usa el resultado en `DATABASE_URL`:
> ```powershell
> .\venv\Scripts\python -c "from urllib.parse import quote; print(quote('TU_CLAVE_POSTGRES', safe=''))"
> ```
> Ejemplo: la clave `mi@clave#1` se escribe `mi%40clave%231`.
>
> Reglas: la base se llama `dogato` (no la cambies); Postgres local usa el puerto `5432` (si instalaste en otro, cámbialo);
> las otras variables del `.env.example` están comentadas con `#` y **no hay que activarlas** en desarrollo.

Guarda y cierra el Bloc de notas.

### 7.5 Arrancar la API
Asegúrate de que **Redis está encendido** (6.4) y luego:
```powershell
.\venv\Scripts\python -m uvicorn main:app --reload
```
Resultado esperado: `Uvicorn running on http://127.0.0.1:8000` y `Application startup complete`. **Deja esta ventana abierta.**

### 7.6 Verificar la API
En el navegador abre **http://localhost:8000/health**. Debe mostrar:
```json
{"status":"ok","postgres":"ok","redis":"ok"}
```
| Si dice… | Significa | Qué hacer |
|---|---|---|
| `"redis":"caido"` | La API no llega a Redis | Enciende Redis (6.4) y revisa `REDIS_PASSWORD` en `.env` |
| Error 500 / no carga | No conecta a Postgres | Revisa `DATABASE_URL` (clave, puerto, codificación de símbolos) y que Postgres esté encendido |

También puedes abrir **http://localhost:8000/docs** (documentación interactiva de todos los endpoints).

---

## 8. Configurar y arrancar el frontend

Abre **otra** ventana de PowerShell (la de la API debe seguir abierta).
```powershell
cd $HOME\Desktop\APP_dog-ato
npm install
copy .env.example .env.local
npm run dev
```
- `npm install` descarga las librerías a la carpeta `node_modules` (la primera vez tarda; no se sube a GitHub).
- `.env.local` contiene `VITE_API_URL=http://localhost:8000` (la dirección de tu API). No necesitas editarlo si la API corre en el puerto 8000.
- `npm run dev` arranca la interfaz en **http://localhost:5173**. Déjala abierta.

> El API solo acepta peticiones desde `http://localhost:5173`. Si el frontend se abre en otro puerto, el login dirá "No se pudo conectar":
> detén lo que ocupa el 5173 o define `CORS_ORIGINS=["http://localhost:PUERTO"]` en el `.env` de la API.

---

## 9. Prueba final: confirmar que todo funciona

9.1 Abre **http://localhost:5173** e inicia sesión con `admin@veterinaria.com` / `Admin12345*`.
Deberías ver el menú **Seguridad** (Veterinarios, Roles, Perfiles, Módulos y permisos) y **Gestión clínica** (Propietarios, Mascotas, Citas, Historial clínico). En la parte inferior izquierda aparece "Credenciales validadas desde PostgreSQL".

9.2 Cierra sesión y entra de nuevo: ahora debe decir **"…desde Redis"** (la credencial salió de la caché de Redis).

9.3 Entra como `andres.gomez@dogato.com` / `Vet12345*`: solo ves **Gestión clínica** (los permisos vienen de la base de datos).

9.4 Mira la sesión dentro de Redis. **(Ubuntu)**:
```bash
redis-cli --user dogato_api --pass TU_CLAVE_REDIS --no-auth-warning
KEYS dogato:*
```
(un comando por línea). Verás llaves como `dogato:sesion:...` y `dogato:cred:...`. Al cerrar sesión en la interfaz, la `sesion` desaparece.

9.5 *(Opcional)* Ejecuta las 48 pruebas automáticas (cada una limpia lo que crea):
```powershell
cd $HOME\Desktop\API_dog-ato
.\venv\Scripts\python -m pytest tests -q
```
Esperado: `48 passed`. Requieren Postgres con la base demo y Redis encendidos.

✅ Si 9.1–9.4 funcionan, tu réplica está lista. Para la demostración de la rúbrica sigue `docs\DEMO_RUBRICA.md`.

---

## 10. Rutina diaria (cada vez que vayas a trabajar)

| Orden | Dónde | Comando |
|---|---|---|
| 1 | Ubuntu | `sudo service redis-server start` |
| 2 | PowerShell (carpeta API) | `.\venv\Scripts\python -m uvicorn main:app --reload` |
| 3 | PowerShell (carpeta frontend) | `npm run dev` |
| 4 | Navegador | http://localhost:5173 |

PostgreSQL arranca solo con Windows. Para actualizar el código: `git pull` en cada carpeta. **Si el equipo cambia `db\DDL.sql`**, vuelve a
ejecutar el paso 3.2 (recrea la base) y reinicia la API.

---

## 11. Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `psql` no se reconoce | `psql.exe` no está en el PATH | Usa la ruta completa (paso 3.2) |
| `password authentication failed for user "postgres"` | Contraseña de Postgres incorrecta | Usa la que definiste al instalar; en `.env` recuerda codificar símbolos (7.4) |
| En la base aparecen tildes dañadas ("MÃ©dico") | Se usó un script viejo | Vuelve a ejecutar `db\DDL.sql` actual (ya corrige la codificación) |
| `sudo: command not found` | Estás en PowerShell/Git Bash o en `docker-desktop` | Abre la app **Ubuntu** (paso 5) |
| `Could not connect to Redis` / `/health` con `"redis":"caido"` | Redis apagado | `sudo service redis-server start` (Ubuntu) |
| `WRONGPASS` | Usuario/clave de Redis distintos a los del `redis.conf` | Alinea `redis.conf` y `.env`; luego `sudo service redis-server restart` |
| Redis no arranca tras editar `redis.conf` | Línea `user default`/`requirepass` duplicada | Comenta la línea antigua (6.3) y mira `sudo tail -n 30 /var/log/redis/redis-server.log` |
| El login dice "No se pudo conectar con el servidor" | API apagada, o frontend en un puerto distinto de 5173 | Arranca la API (7.5) y revisa 8 |
| El login dice "El servicio de sesiones no está disponible" | Redis apagado | Enciéndelo (6.4) |
| El login dice "Demasiados intentos fallidos" | 5 contraseñas malas seguidas (bloqueo 15 min) | Espera, o en Redis: `DEL dogato:intentos:correo@ejemplo.com` |
| `Activate.ps1 ... ejecución de scripts deshabilitada` | Política de PowerShell | No actives el venv: usa `.\venv\Scripts\python ...` |
| `ModuleNotFoundError` al arrancar la API | No instalaste las librerías o no existe `venv` | Repite 7.3 |
| `npm` no se reconoce | Node.js no instalado | Instálalo (1.3) y abre una PowerShell nueva |
| Windows no llega a Redis (`TcpTestSucceeded : False`) | Redis apagado o WSL1 | `wsl -l -v` debe mostrar VERSION 2; enciende Redis |

---

## 12. Instrucciones para un asistente de IA

> Esta sección está escrita **para un modelo de IA** (con o sin acceso a terminal). Si lo usas como guía conversacional, pégale el
> prompt de 12.1 junto con el contenido de este archivo.

### 12.1 Prompt listo para copiar
```text
Eres un asistente técnico. Ayúdame a instalar en mi PC (Windows 10/11) una réplica funcional del proyecto DOG-ATO siguiendo
EXACTAMENTE el archivo INSTALACION_COMPANEROS.md (adjunto). Reglas:
1. Avanza paso a paso, en el orden del archivo, y confirma el resultado esperado de cada paso antes de continuar.
2. NO inventes comandos, rutas ni versiones: usa los del archivo. Si algo falla, usa la tabla de "Problemas frecuentes" y pide el mensaje exacto.
3. Pídeme (no adivines) estos datos: mi contraseña de PostgreSQL, la versión de PostgreSQL instalada, la contraseña de Redis que quiero usar
   y la carpeta donde clonar. No me las pidas por repetido ni las escribas en archivos que se suban a git.
4. NUNCA hagas commit del archivo .env ni de .env.local. NUNCA hagas push. Solo trabajas en mi máquina.
5. Aviso importante: db/DDL.sql BORRA y recrea la base "dogato"; pídeme confirmación antes de ejecutarlo.
6. Al terminar ejecuta la lista de verificación de la sección 12.3 y dame un resumen: qué quedó OK y qué no.
```

### 12.2 Contexto técnico (para el modelo)
- **Repositorios** (rama `main`): `https://github.com/juancarvajal14/API_dog-ato.git` y `https://github.com/juancarvajal14/APP_dog-ato.git`.
  Deben quedar como carpetas hermanas. Contexto ampliado del proyecto: `API_dog-ato/CONTEXT.md`.
- **Stack:** PostgreSQL ≥ 13 (Windows) · Redis nativo en Ubuntu/WSL2 (sin Docker) · API Python (FastAPI + SQLAlchemy + psycopg 3 + redis + bcrypt) · Frontend React 19 + Vite.
- **Puertos:** Postgres 5432 · Redis 6379 · API 8000 · Frontend 5173 (el CORS del API solo permite `http://localhost:5173` por defecto).
- **Archivos que el usuario debe crear (NUNCA van a git):**
  - `API_dog-ato/.env` (copiar de `.env.example`) con exactamente estas variables activas: `DATABASE_URL`, `REDIS_HOST`, `REDIS_PORT`, `REDIS_USER`, `REDIS_PASSWORD`.
    Formato de `DATABASE_URL`: `postgresql+psycopg://postgres:<clave URL-codificada>@localhost:5432/dogato`. Codificar la clave con
    `urllib.parse.quote(clave, safe='')` si tiene símbolos.
  - `APP_dog-ato/.env.local` (copiar de `.env.example`): `VITE_API_URL=http://localhost:8000`.
  - `API_dog-ato/venv/` (entorno virtual): `python -m venv venv` y `.\venv\Scripts\python -m pip install -r requirements-dev.txt`.
- **Redis:** usuario ACL `dogato_api` con la contraseña elegida por el usuario; `user default off`; escucha en `127.0.0.1`. Esa MISMA contraseña
  va en `REDIS_PASSWORD`. La contraseña de Redis no debe contener espacios (usar `[A-Za-z0-9_-]`).
- **Base de datos:** se crea ÚNICAMENTE con `psql -U postgres -f db\DDL.sql` (no con pgAdmin ni con otros archivos; no existe otro `.sql`).
  Es destructivo para la BD `dogato` y no destructivo para el resto del servidor.
- **No usar:** Docker para Redis, `sudo` en PowerShell, ni scripts distintos a los de esta guía.

### 12.3 Lista de verificación (criterios de aceptación)
Ejecutar y comprobar, en este orden:
1. `psql -U postgres -d dogato -tA -c "select count(*) from usuario"` → `4`.
2. `psql -U postgres -d dogato -tA -c "select count(*) from fn_menu_usuario((select id_usuario from usuario where email='admin@veterinaria.com'))"` → `10`.
3. En Ubuntu: `redis-cli ping` → `NOAUTH Authentication required.` y `redis-cli --user dogato_api --pass <clave> --no-auth-warning ping` → `PONG`.
4. PowerShell: `Test-NetConnection localhost -Port 6379` → `TcpTestSucceeded : True`.
5. `GET http://localhost:8000/health` → `{"status":"ok","postgres":"ok","redis":"ok"}`.
6. `POST http://localhost:8000/auth/login` con `{"email":"admin@veterinaria.com","password":"Admin12345*"}` → HTTP 200 con `access_token`, `menu` (2 carpetas) y `origen_credenciales: "postgres"`; repetirlo → `"redis"`.
7. `GET http://localhost:5173` → 200 y el login funciona en el navegador.
8. (Opcional) `.\venv\Scripts\python -m pytest tests -q` → `48 passed`.
9. `git status` en ambos repos no debe mostrar `.env` ni `.env.local` (están ignorados).

### 12.4 Cuándo detenerse y preguntar
- Falta o es ambigua una contraseña, la versión de Postgres o la carpeta de instalación.
- Existe una base `dogato` que el usuario podría querer conservar (avisar antes del paso 3).
- Un comando devuelve un error no contemplado en "Problemas frecuentes": mostrar el mensaje completo y proponer un diagnóstico, no improvisar cambios en el código.
- El usuario tiene un sistema distinto de Windows: adaptar rutas y comandos (WSL no aplica en Linux/macOS; ahí Redis se instala con el gestor de paquetes
  local y la sintaxis de `redis.conf` es la misma), manteniendo las mismas variables de `.env`.
