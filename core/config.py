from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_user: str = "dogato_api"
    redis_password: str
    redis_ssl: bool = False  # True para Redis administrado con TLS (p. ej. Upstash)

    # "produccion" desactiva la documentación interactiva (/docs, /redoc)
    entorno: str = "desarrollo"

    # Sesión y protección del login (tiempos en segundos)
    sesion_ttl: int = 8 * 3600
    credenciales_ttl: int = 10 * 60
    max_intentos_login: int = 5
    bloqueo_login_ttl: int = 15 * 60

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
