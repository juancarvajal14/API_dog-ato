from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.errors import ErrorNegocio
from core.redis_client import redis_disponible
from routers import auth, catalogos, citas, historial, mascotas, modulos, perfiles, propietarios, roles, veterinarios

en_produccion = settings.entorno == "produccion"
app = FastAPI(
    title="DOG-ATO API",
    docs_url=None if en_produccion else "/docs",
    redoc_url=None if en_produccion else "/redoc",
    openapi_url=None if en_produccion else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ErrorNegocio)
def manejar_error_negocio(_: Request, error: ErrorNegocio):
    return JSONResponse(status_code=error.status_code, content={"detail": error.detail}, headers=error.headers)


for router in (auth, catalogos, propietarios, mascotas, citas, historial, veterinarios, roles, perfiles, modulos):
    app.include_router(router.router)


@app.get("/health", tags=["Sistema"])
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "postgres": "ok", "redis": "ok" if redis_disponible() else "caido"}
