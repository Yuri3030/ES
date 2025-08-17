# app/database.py
from __future__ import annotations

# app/database.py
from __future__ import annotations

import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.settings import get_settings

# 1) Monta a URL:
#    - prioriza Settings.DATABASE_URL
#    - cai para variável de ambiente DATABASE_URL
#    - por fim monta com os POSTGRES_* (útil em dev/docker)
settings = get_settings()

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "appdb")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "db")

default_url = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}"
DATABASE_URL = getattr(settings, "DATABASE_URL", None) or os.getenv("DATABASE_URL") or default_url
# ↑ psycopg2-binary => use "postgresql://..."

# 2) Engine e sessão
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

# 3) Base com naming convention (opcional, mas ajuda o Alembic)
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = MetaData(naming_convention=NAMING_CONVENTION)
Base = declarative_base(metadata=metadata)

# 4) Dependency do FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


