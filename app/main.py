from fastapi import FastAPI, Depends, HTTPException,APIRouter, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.database import Base, engine, get_db, engine
# Importa os modelos necessários
from app import models
from app.models import User
# Importa schemas necessários
from app.schemas import UserCreate, UserResponse, PasswordResetRequest, PasswordResetConfirm
from app.schemas import LoginRequest, LoginResponse
# Importa a função de criação de token

from app.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
from typing import List, Optional
from datetime import datetime
# para conseguir o autorization automático no sweagger
from fastapi.security import OAuth2PasswordRequestForm
# para a criação do administrador padrão
from app.database import SessionLocal
from app.models import User, Mood

# para receber o email no corpo da requisição
from fastapi import Body

from app.schemas import MoodCreate, MoodResponse
from app.models import User, Reminder
from app.schemas import ReminderCreate, ReminderResponse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import secrets
from datetime import datetime, timedelta, timezone
from app.models import User, PasswordResetToken

from app.database import SessionLocal
from app.models import EmergencyContact
from app.database import get_db
from app.models import EmergencyContact
from app.schemas import EmergencyContactCreate, EmergencyContactResponse
from app.auth import get_current_user
# Cria as tabelas automaticamente

#Base.metadata.create_all(bind=engine)



app = FastAPI()

# Permite qualquer origem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cuidado: isso libera para qualquer site
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Config para hash de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

#  função para verificar a senha
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Rota inicial
@app.get("/")
def root():
    return {"message": "🚀 FastAPI + PostgreSQL funcionando!"}

# Rota para obter usuário atual
# Esta rota usa a dependência get_current_user para obter o usuário autenticado
@app.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "date_of_birth": current_user.date_of_birth   
    }

# Rota para criar usuário
@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Verifica se email já existe
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    # Cria novo usuário
    new_user = models.User(
        name=user.name,
        email=user.email,
        password_hash=hash_password(user.password),
        date_of_birth=user.date_of_birth 
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Rota para listar usuários
@app.get("/users/", response_model=list[UserResponse])
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Acesso restrito ao administrador.")
    
    return db.query(models.User).all()

# Rota para deletar usuário pelo email
@app.delete("/users/")
def delete_user(
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Apenas o administrador pode deletar usuários")

    user = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.deleted_at = datetime.utcnow()
    user.is_active = False
    db.commit()
    return {"message": "Usuário marcado como excluído"}




# Rota de login
@app.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    #   Buscar usuário pelo e-mail
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")

    #   Gerar JWT com expiração
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    return LoginResponse(
        message="Login realizado com sucesso!",
        token=access_token
    )

@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    #  Buscar usuário
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")

    #  Gerar JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    #  Formato padrão OAuth2
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
RESET_TOKEN_EXPIRE_MINUTES = 60  # 1h

@app.post("/password-reset/request")
def password_reset_request(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    # Por segurança, não revelamos se o e-mail existe ou não.
    # Se existir, criamos o token; se não, retornamos a mesma mensagem.

    if user:
        # invalida tokens antigos ainda não usados (opcional)
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None)
        ).delete(synchronize_session=False)

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)

        db.add(PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        ))
        db.commit()

        # Aqui você enviaria email com o token. Em DEV, retornamos o token:
        return {
            "message": "Se o e-mail existir, enviaremos instruções para redefinir a senha.",
            "dev_token": token,  # REMOVA em produção
            "expires_in_minutes": RESET_TOKEN_EXPIRE_MINUTES
        }

    return {"message": "Se o e-mail existir, enviaremos instruções para redefinir a senha."}


@app.post("/password-reset/confirm")
def password_reset_confirm(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    prt = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == payload.token
    ).first()

    if not prt:
        raise HTTPException(status_code=400, detail="Token inválido")

    if prt.used_at is not None:
        raise HTTPException(status_code=400, detail="Token já utilizado")

    now = datetime.now(timezone.utc)
    if prt.expires_at < now:
        raise HTTPException(status_code=400, detail="Token expirado")

    user = db.query(User).filter(User.id == prt.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # atualiza senha
    user.password_hash = hash_password(payload.new_password)
    prt.used_at = now

    db.commit()

    return {"message": "Senha redefinida com sucesso."}

# cria um usuário administrador padrão se não existir

def create_default_admin():
    db: Session = SessionLocal()
    admin_email = "admin@example.com"
    admin_password = "admin"

    if not db.query(User).filter(User.email == admin_email).first():
        new_admin = User(
            name="Administrador",
            email=admin_email,
            password_hash=hash_password(admin_password),
            is_active=True
        )
        db.add(new_admin)
        db.commit()
    db.close()

create_default_admin()


# Criar registro de humor (do usuário logado)
@app.post("/moods", response_model=MoodResponse)
def create_mood(payload: MoodCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entry = Mood(
        user_id=current_user.id,
        score=payload.score,
        mood_type=payload.mood_type,
        comment=payload.comment
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

# Listar meus registros de humor
@app.get("/moods", response_model=list[MoodResponse])
def list_my_moods(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Mood).filter(Mood.user_id == current_user.id).order_by(Mood.created_at.desc()).all()

# (Opcional) Admin lista humores de um usuário específico por e-mail
@app.get("/users/{email}/moods", response_model=list[MoodResponse])
def list_user_moods_as_admin(
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.email != "admin@example.com":
        raise HTTPException(status_code=403, detail="Apenas o administrador pode acessar os registros de outros usuários.")

    target = db.query(User).filter(User.email == email).first()
    if not target:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return db.query(Mood).filter(Mood.user_id == target.id).order_by(Mood.created_at.desc()).all()# criar lembrete

# criar lembrete
@app.post("/reminders", response_model=ReminderResponse)
def create_reminder(
    payload: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reminder = Reminder(
        user_id=current_user.id,
        message=payload.message,
        due_at=payload.due_at,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder

# listar só meus lembretes
@app.get("/reminders", response_model=list[ReminderResponse])
def list_my_reminders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Reminder)
        .filter(Reminder.user_id == current_user.id)
        .order_by(Reminder.due_at.asc())
        .all()
    )

# marcar como feito / desfazer
@app.patch("/reminders/{reminder_id}/done", response_model=ReminderResponse)
def toggle_done(
    reminder_id: int,
    done: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reminder = (
        db.query(Reminder)
        .filter(Reminder.id == reminder_id, Reminder.user_id == current_user.id)
        .first()
    )
    if not reminder:
        raise HTTPException(status_code=404, detail="Lembrete não encontrado")
    reminder.done = done
    db.commit()
    db.refresh(reminder)
    return reminder

# deletar lembrete
@app.delete("/reminders/{reminder_id}")
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reminder = (
        db.query(Reminder)
        .filter(Reminder.id == reminder_id, Reminder.user_id == current_user.id)
        .first()
    )
    if not reminder:
        raise HTTPException(status_code=404, detail="Lembrete não encontrado")
    db.delete(reminder)
    db.commit()
    return {"message": "Lembrete deletado com sucesso"}


DEFAULT_BR_CONTACTS = [
    {"name": "Polícia Militar", "phone": "190", "category": "seguranca"},
    {"name": "SAMU (Ambulância)", "phone": "192", "category": "saude"},
    {"name": "Bombeiros", "phone": "193", "category": "seguranca"},
    {"name": "Defesa Civil", "phone": "199", "category": "defesa"},
    {"name": "Delegacia da Mulher", "phone": "180", "category": "direitos"},
    {"name": "Disque Denúncia", "phone": "181", "category": "seguranca"},
    {"name": "CVV - Prevenção ao Suicídio", "phone": "188", "category": "saude"},
    {"name": "PRF - Polícia Rodoviária Federal", "phone": "191", "category": "seguranca"},
    {"name": "Disque Saúde (SUS)", "phone": "136", "category": "saude"},
]

def ensure_default_emergency_contacts():
    db: Session = SessionLocal()
    try:
        # verifica se já existe algum default
        exists = db.query(EmergencyContact).filter(
            EmergencyContact.is_default.is_(True),
            EmergencyContact.deleted_at.is_(None)
        ).first()
        if exists:
            return

        for c in DEFAULT_BR_CONTACTS:
            db.add(EmergencyContact(
                user_id=None,
                name=c["name"],
                phone=c["phone"],
                category=c.get("category"),
                is_default=True
            ))
        db.commit()
    finally:
        db.close()

def is_admin(user) -> bool:
    # adapte à sua lógica; ex: admin por email
    return user.email == "admin@example.com"

@app.get("/{contact_id}", response_model=List[EmergencyContactResponse])
def list_all_contacts(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Lista contatos padrão + contatos do usuário logado (soft-delete ignorado)."""
    q = db.query(EmergencyContact).filter(EmergencyContact.deleted_at.is_(None)).filter(
        (EmergencyContact.is_default.is_(True)) |
        (EmergencyContact.user_id == current_user.id)
    ).order_by(EmergencyContact.is_default.desc(), EmergencyContact.name.asc())
    return q.all()

@app.post("/{contact_id}", response_model=EmergencyContactResponse, status_code=201)
def create_contact(
    payload: EmergencyContactCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Cria um contato pessoal do usuário."""
    ec = EmergencyContact(
        user_id=current_user.id,
        name=payload.name,
        phone=payload.phone,
        category=payload.category,
        is_default=False
    )
    db.add(ec)
    db.commit()
    db.refresh(ec)
    return ec

@app.delete("/{contact_id}", status_code=200)
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Soft delete: só pode deletar seus contatos; admin pode deletar qualquer um."""
    ec = db.query(EmergencyContact).filter(EmergencyContact.id == contact_id).first()
    if not ec or ec.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Contato não encontrado")

    if ec.is_default and not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Apenas admin pode excluir contatos padrão")

    if (not ec.is_default) and (ec.user_id != current_user.id) and (not is_admin(current_user)):
        raise HTTPException(status_code=403, detail="Sem permissão para excluir este contato")

    ec.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": "Contato excluído com sucesso (soft delete)."}

# registre o router no app principal
# app.include_router(router_ec)