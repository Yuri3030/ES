from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# ✅ Importa a URL do banco e os modelos
from app.database import SQLALCHEMY_DATABASE_URL
from app.models import Base

# Este objeto dá acesso às configs do alembic.ini
config = context.config

# ✅ Força a URL a ser a mesma da aplicação
config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)

# Configuração de log
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ✅ Passa o metadata dos modelos para o Alembic
target_metadata = Base.metadata

def run_migrations_offline():
    """Modo offline gera apenas scripts sem conectar no DB"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Modo online conecta no DB e aplica/gera migração"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # ✅ Detecta alterações no tipo da coluna
        )

        with context.begin_transaction():
            context.run_migrations()

# Decide se roda offline ou online
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
