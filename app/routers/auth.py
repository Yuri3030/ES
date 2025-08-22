# app/routers/auth.py (ou onde estiver sua rota)
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Pessoa
from app.auth import create_access_token, verify_password
from app.core.settings import get_settings
from app.schemas import TokenResponse , LoginRequest



router = APIRouter(tags=["auth"])

@router.post("/token", response_model=TokenResponse)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    pessoa = db.query(Pessoa).filter(Pessoa.email == form_data.username).first()
    if not pessoa or not verify_password(form_data.password, pessoa.password_hash or ""):
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail ou senha inválidos",
        )

    settings = get_settings()
    access_token = create_access_token(
        data={"sub": pessoa.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=TokenResponse)
def login_json(payload: LoginRequest, db: Session = Depends(get_db)):
    pessoa = db.query(Pessoa).filter(Pessoa.email == payload.email).first()
    if not pessoa or not verify_password(payload.password, pessoa.password_hash or ""):
        #  seu requisito: 400 em caso de credenciais inválidas
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail ou senha inválidos")

    settings = get_settings()
    token = create_access_token(
        data={"sub": pessoa.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": token, "token_type": "bearer"}
  
