from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date
from enum import Enum
from typing import Optional

# -------- login --------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# -------- Pessoas --------

class PessoaCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=6)   # <- senha enviada no cadastro
    date_of_birth: date | None = None

class PessoaResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    date_of_birth: date | None = None

    model_config = {"from_attributes": True}  # pydantic v2


# -------- Check-ins --------
class CheckInType(str, Enum):
    alegria = "alegria"
    tristeza = "tristeza"
    angustia = "angustia"
    magoa = "mágoa"
    ansiedade = "ansiedade"

class CheckInCreate(BaseModel):
    score: int = Field(..., ge=1, le=5)
    checkin_type: CheckInType
    comment: Optional[str] = None

class CheckInResponse(BaseModel):
    id: int
    score: int
    checkin_type: CheckInType
    comment: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}

# -------- Lembretes --------
class LembreteCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=280)
    due_at: datetime

class LembreteResponse(BaseModel):
    id: int
    message: str
    due_at: datetime
    done: bool
    created_at: datetime
    model_config = {"from_attributes": True}

# -------- Contatos de Emergência --------
class ContatoEmergenciaBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    phone: str = Field(..., min_length=2, max_length=30)
    category: Optional[str] = None

class ContatoEmergenciaCreate(ContatoEmergenciaBase):
    pass

class ContatoEmergenciaResponse(ContatoEmergenciaBase):
    id: int
    is_default: bool
    created_at: datetime
    deleted_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# -------- autenticação --------
class SignupCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=6)
    date_of_birth: date | None = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"