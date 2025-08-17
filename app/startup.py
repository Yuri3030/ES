# app/startup.py
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.auth import hash_password
from app.core.settings import get_settings
from app.models import Pessoa
from app.routers.contatos_emergencia import ensure_default_emergency_contacts  # <- nome novo

def ensure_admin():
    """Cria admin default se não existir (idempotente)."""
    s = get_settings()
    email = getattr(s, "ADMIN_EMAIL", "admin@example.com")
    pwd   = getattr(s, "ADMIN_PASSWORD", "admin")

    db: Session = SessionLocal()
    try:
        if not db.query(Pessoa).filter(Pessoa.email == email).first():
            db.add(Pessoa(name="Administrador", email=email,
                          password_hash=hash_password(pwd), is_active=True))
            db.commit()
    finally:
        db.close()

def run_startup_tasks():
    ensure_admin()
    ensure_default_emergency_contacts()
