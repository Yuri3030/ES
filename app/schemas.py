from pydantic import BaseModel, EmailStr
from pydantic import  conint
from datetime import datetime, date
from enum import Enum
from pydantic import  Field
from typing import Optional


# Modelo para entrada de cadastro
class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    date_of_birth: date | None = None  

# Modelo para resposta (não retorna a senha)
class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    date_of_birth: date | None = None
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True


# Modelo para login
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Modelo para resposta de login
class LoginResponse(BaseModel):
    message: str
    token: str | None = None  

# Modelos para Mood
class MoodType(str, Enum):
    alegria = "alegria"
    tristeza = "tristeza"
    angustia = "angustia"
    magoa = "mágoa"
    ansiedade = "ansiedade"

class MoodCreate(BaseModel):
    score: int = Field(..., ge=1, le=5)
    mood_type: MoodType  # <-- escolha obrigatória
    comment: Optional[str] = None

class MoodResponse(BaseModel):
    id: int
    score: int
    mood_type: MoodType
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# Modelo para lembrete

class ReminderCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=280)
    # envie no formato ISO 8601 (ex.: "2025-08-10T14:00:00Z")
    due_at: datetime

class ReminderResponse(BaseModel):
    id: int
    message: str
    due_at: datetime
    done: bool
    created_at: datetime

    class Config:
        from_attributes = True  # pydantic v2

# Modelo para reset de senha
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str = Field(..., min_length=10)
    new_password: str = Field(..., min_length=6)