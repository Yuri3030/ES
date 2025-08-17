# migrations/env.py
from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# --- garantir que /app esteja no sys.path (raiz do projeto) ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# --- sua app: Base + modelos (para autogenerate) ---
from app.database import Base  # Base com naming_convention
import app.models  # noqa: F401  (não remover: registra as tabelas no metadata)

# objeto de config do Alembic
config = context.config

# logging do Alembic (opcional, mas útil)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# metadata alvo para autogenerate
target_metadata = Base.metadata

# ---- URL do banco: ler do ambiente (psycopg2-binary -> postgresql://) ----
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/appdb")
config.set_main_option("sqlalchemy.url", DATABASE_URL)

def run_migrations_offline() -> None:
    """Execução offline (gera SQL sem conectar)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Execução online (conecta no banco e aplica/gera diffs)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,            # detecta mudanças de tipo
            compare_server_default=True,  # detecta mudanças de server_default
            # include_object=include_object,  # habilite se quiser filtrar objetos
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
