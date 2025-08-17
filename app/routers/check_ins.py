# app/routers/check_ins.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CheckIn, Pessoa as PessoaModel
from app.schemas import CheckInCreate, CheckInResponse
from app.security.deps import require_owner

router = APIRouter(prefix="/pessoas/{pessoa_id}/check_ins", tags=["check_ins"])

@router.get("", response_model=List[CheckInResponse])
def listar_check_ins(
    pessoa_id: int,
    db: Session = Depends(get_db),
    current: PessoaModel = Depends(require_owner),
):
    return (
        db.query(CheckIn)
        .filter(CheckIn.pessoa_id == pessoa_id)
        .order_by(CheckIn.created_at.desc())
        .all()
    )

@router.post("", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
def criar_check_in(
    pessoa_id: int,
    payload: CheckInCreate,
    db: Session = Depends(get_db),
    current: PessoaModel = Depends(require_owner),
):
    entry = CheckIn(
        pessoa_id=pessoa_id,
        score=payload.score,
        checkin_type=payload.checkin_type,
        comment=payload.comment,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
