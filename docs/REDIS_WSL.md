# Redis nativo en WSL2 (Ubuntu) — guía para cada integrante

Redis solo se usa para el login (sesiones, intentos fallidos, caché de credenciales). Corre dentro de Ubuntu en WSL2; el API en Windows lo alcanza por `localhost:6379`.

## 1. Instalar Ubuntu en WSL (una sola vez)
En **PowerShell como administrador**:
```powershell
wsl --install -d Ubuntu
```
Reinicia el PC si lo pide. Al abrir "Ubuntu" por primera vez crea un usuario y contraseña de Linux (apúntalos; `sudo` te pedirá esa contraseña).
Si ya tienes WSL pero solo la distro `docker-desktop` (`wsl -l -v`), igual debes instalar Ubuntu: `docker-desktop` es interna y no trae `sudo` ni `apt`.
Comprueba que sea WSL 2: `wsl -l -v` → columna VERSION = 2.

## 2. Instalar Redis (dentro de Ubuntu)
Abre la app **Ubuntu** (o `wsl -d Ubuntu`) y ejecuta:
```bash
sudo apt update
sudo apt install -y redis-server
redis-server --version
```

## 3. Configurar usuario y contraseña (ACL)
Elige una contraseña larga (`TU_CLAVE`). El mismo valor va en el `.env` del API (`REDIS_PASSWORD`).
```bash
sudo tee -a /etc/redis/redis.conf > /dev/null <<'EOF'

# --- DOG-ATO ---
bind 127.0.0.1 -::1
protected-mode yes
user default off
user dogato_api on >TU_CLAVE ~* &* +@all
EOF
```
(Sustituye `TU_CLAVE` antes de ejecutar. Si ya existía una línea `user default ...` o `requirepass` en el archivo, bórrala o coméntala con `sudo nano /etc/redis/redis.conf`.)

## 4. Encender Redis
```bash
sudo service redis-server start
sudo service redis-server status      # debe decir "active (running)" o "redis-server is running"
```
Otros comandos: `sudo service redis-server stop` / `restart`.
Para que arranque solo al abrir Ubuntu (opcional, si tu WSL tiene systemd): `sudo systemctl enable redis-server`. Si no, repite `sudo service redis-server start` cada vez que enciendas el PC y abras Ubuntu.

## 5. Probar el acceso (evidencia para la rúbrica: ≥ 3 instrucciones)
```bash
redis-cli ping                                    # → (error) NOAUTH Authentication required  (sin credenciales falla: correcto)
redis-cli --user dogato_api --pass TU_CLAVE --no-auth-warning
```
Dentro de `redis-cli`:
```
PING                                  → PONG
ACL WHOAMI                            → "dogato_api"
SET dogato:prueba "hola" EX 60        → OK
GET dogato:prueba                     → "hola"
TTL dogato:prueba                     → 59
HSET dogato:sesion:demo email a@b.com
HGETALL dogato:sesion:demo
KEYS dogato:*
DEL dogato:prueba dogato:sesion:demo
EXIT
```
Capturas sugeridas: `redis-server --version`, el estado del servicio, el `NOAUTH` sin credenciales y estas instrucciones con credenciales.

## 6. Conectar el API (Windows)
En `.env` del API:
```
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_USER=dogato_api
REDIS_PASSWORD=TU_CLAVE
```
Prueba desde PowerShell (Windows) con Python cuando exista el API, o simplemente verifica que el puerto responda: `Test-NetConnection localhost -Port 6379`.
Si `localhost` no llegara a Redis, usa `wsl hostname -I` para obtener la IP de Ubuntu y ponla en `REDIS_HOST`.

## Problemas frecuentes
| Síntoma | Causa / solución |
|---|---|
| `sudo: command not found` | Estás en `docker-desktop`, PowerShell o Git Bash. Abre la app **Ubuntu**. |
| `Could not connect to Redis` | Falta `sudo service redis-server start`. |
| `WRONGPASS` | Usuario o clave distintos a los del `redis.conf`. Tras editar el archivo: `sudo service redis-server restart`. |
| El servicio no arranca | Revisa `sudo tail -n 30 /var/log/redis/redis-server.log` (suele ser una línea duplicada de `user default` en `redis.conf`). |
| Windows no llega a Redis | Verifica WSL 2 y que Redis esté en `bind 127.0.0.1`; prueba `Test-NetConnection localhost -Port 6379`. |
