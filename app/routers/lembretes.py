# app/routers/lembretes.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lembrete, Pessoa as PessoaModel
from app.schemas import LembreteCreate, LembreteResponse
from app.security.deps import require_owner

router = APIRouter(prefix="/pessoas/{pessoa_id}/lembretes", tags=["lembretes"])

@router.get("", response_model=List[LembreteResponse])
def listar_lembretes(
    pessoa_id: int,
    db: Session = Depends(get_db),
    current: PessoaModel = Depends(require_owner),
):
    return (
        db.query(Lembrete)
        .filter(Lembrete.pessoa_id == pessoa_id)
        .order_by(Lembrete.due_at.asc())
        .all()
    )

@router.post("", response_model=LembreteResponse, status_code=status.HTTP_201_CREATED)
def criar_lembrete(
    pessoa_id: int,
    payload: LembreteCreate,
    db: Session = Depends(get_db),
    current: PessoaModel = Depends(require_owner),
):
    lemb = Lembrete(pessoa_id=pessoa_id, message=payload.message, due_at=payload.due_at)
    db.add(lemb)
    db.commit()
    db.refresh(lemb)
    return lemb

@router.patch("/{lembrete_id}/done", response_model=LembreteResponse)
def marcar_feito(
    pessoa_id: int,
    lembrete_id: int,
    done: bool = True,
    db: Session = Depends(get_db),
    current: PessoaModel = Depends(require_owner),
):
    lemb = (
        db.query(Lembrete)
        .filter(Lembrete.id == lembrete_id, Lembrete.pessoa_id == pessoa_id)
        .first()
    )
    if not lemb:
        raise HTTPException(status_code=404, detail="Lembrete não encontrado")
    lemb.done = done
    db.commit()
    db.refresh(lemb)
    return lemb

@router.delete("/{lembrete_id}", status_code=200)
def delete_lembrete(
    pessoa_id: int,
    lembrete_id: int,
    db: Session = Depends(get_db),
    current: PessoaModel = Depends(require_owner),
):
    lemb = (
        db.query(Lembrete)
        .filter(Lembrete.id == lembrete_id, Lembrete.pessoa_id == pessoa_id)
        .first()
    )
    if not lemb:
        raise HTTPException(status_code=404, detail="Lembrete não encontrado")
    db.delete(lemb)
    db.commit()
    return {"message": "Lembrete deletado com sucesso"}
