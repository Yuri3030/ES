# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.settings import get_settings
from contextlib import asynccontextmanager
from app.models import Pessoa
from app.auth import hash_password

from app.routers.pessoas import router as pessoas_router
from app.routers.check_ins import router as check_ins_router
from app.routers.lembretes import router as lembretes_router
from app.routers.contatos_emergencia import router as contatos_emergencia_router
from app.routers.contatos_emergencia import ensure_default_emergency_contacts
from app.routers.auth import router as auth_router



ADMIN_EMAIL = "admin@example.com"  
ADMIN_PASS  = "admin"

def ensure_admin():
    db = SessionLocal()
    try:
        if not db.query(Pessoa).filter(Pessoa.email == ADMIN_EMAIL).first():
            db.add(Pessoa(
                name="Administrador",
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASS),
                is_active=True,
            ))
            db.commit()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # popula contatos padrão uma única vez (idempotente)
    ensure_default_emergency_contacts()
    yield


settings = get_settings()
app = FastAPI(title=getattr(settings, "APP_NAME", "Minha API"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "🚀 FastAPI + PostgreSQL funcionando! (sem autenticação)"}

# registra novos routers
app.include_router(auth_router)
app.include_router(pessoas_router)
app.include_router(check_ins_router)
app.include_router(lembretes_router)
app.include_router(contatos_emergencia_router)



# seed dos contatos padrão
@app.on_event("startup")
def on_startup():
    ensure_default_emergency_contacts()
