# app/routers/pessoas.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Pessoa
from app.schemas import PessoaCreate, PessoaResponse
from app.auth import hash_password, get_current_pessoa
from app.security.deps import require_owner

router = APIRouter(prefix="/pessoas", tags=["pessoas"])
@router.get("/me/id")
def get_meu_id(current: Pessoa = Depends(get_current_pessoa)):
    return {"id": current.id}

@router.post("", response_model=PessoaResponse, status_code=status.HTTP_201_CREATED)
def criar_pessoa(payload: PessoaCreate, db: Session = Depends(get_db)):
    if db.query(Pessoa).filter(Pessoa.email == payload.email).first():
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    pessoa = Pessoa(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        date_of_birth=payload.date_of_birth,
        is_active=True,
    )
    db.add(pessoa)
    db.commit()
    db.refresh(pessoa)
    return pessoa

@router.get("/me", response_model=PessoaResponse)
def me(current: Pessoa = Depends(get_current_pessoa)):
    return current


@router.delete("/{pessoa_id}", status_code=200)
def delete_pessoa(pessoa_id: int, db: Session = Depends(get_db), current: Pessoa = Depends(require_owner)):
    pessoa = db.query(Pessoa).get(pessoa_id)
    if not pessoa:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    pessoa.deleted_at = func.now()
    pessoa.is_active = False
    db.commit()
    return {"message": "Conta marcada como excluída"}
