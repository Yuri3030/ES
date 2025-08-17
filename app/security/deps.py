# app/security/deps.py
from fastapi import Depends, HTTPException, status
from app.auth import get_current_pessoa
from app.models import Pessoa as PessoaModel

def require_owner(pessoa_id: int, current: PessoaModel = Depends(get_current_pessoa)) -> PessoaModel:
    if current.id != pessoa_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: recurso de outra pessoa.",
        )
    return current
