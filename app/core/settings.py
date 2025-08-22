# app/core/settings.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    # App
    APP_NAME: str = "Minha API"
    ENVIRONMENT: str = "dev"

    # Banco (psycopg2-binary => postgresql://)
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/appdb"

    #  JWT
    SECRET_KEY: str = "CHANGE_ME_SUPER_SECRET_KEY"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    ALLOWED_ORIGINS: str = "*"
    def allowed_origins_list(self) -> List[str]:
        raw = self.ALLOWED_ORIGINS
        if raw.strip() == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()

# (opcional) exportar uma instância direta
settings = get_settings()



class Settings(BaseSettings):
    SECRET_KEY: str = "CHANGE_ME_SUPER_SECRET_KEY"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
