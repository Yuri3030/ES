from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.database import Base, engine, get_db
# Importa os modelos necessários
from app import models
from app.models import User
# Importa schemas necessários
from app.schemas import UserCreate, UserResponse
from app.schemas import LoginRequest, LoginResponse
# Importa a função de criação de token
from datetime import timedelta
from app.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user

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


# Cria as tabelas automaticamente
#Base.metadata.create_all(bind=engine)

app = FastAPI()

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
        "created_at": current_user.created_at
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
        password_hash=hash_password(user.password)
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

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    db.delete(user)
    db.commit()
    return {"message": f"Usuário {email} deletado com sucesso"}




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


