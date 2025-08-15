from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from app.database import Base  # ✅ Base vem daqui
from sqlalchemy import Column, Integer, String, ForeignKey, CheckConstraint, func
from sqlalchemy.orm import relationship, backref
import enum
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Column, Integer,  Boolean, ForeignKey, func

from sqlalchemy import Column, Date
from datetime import datetime

# app/models.py# Importa a Base do arquivo database.py para definir os modelos
# Define o modelo User 
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    date_of_birth = Column(Date, nullable=True)  
    deleted_at = Column(DateTime, nullable=True)
# Define o modelo MoodType como uma Enumeração
class MoodType(str, enum.Enum):
    alegria = "alegria"
    tristeza = "tristeza"
    angustia = "angustia"
    magoa = "mágoa"
    ansiedade = "ansiedade"
# Define o modelo Mood
class Mood(Base):
    __tablename__ = "moods"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    mood_type = Column(SqlEnum(MoodType), nullable=False)  # <-- novo campo
    comment = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("score >= 1 AND score <= 5", name="ck_moods_score_range"),
    )

    user = relationship(
        "User",
        backref=backref("moods", cascade="all, delete-orphan")
    )

# Modelo para lembretes
class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message = Column(String, nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=False)
    done = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", backref=backref("reminders", cascade="all, delete-orphan"))

# Modelo para tokens de redefinição de senha
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User")

# Modelo para contatos de emergência
class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(Integer, primary_key=True, index=True)
    # se for um contato global (padrão), user_id = None e is_default = True
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    name = Column(String, nullable=False)        # ex: "Polícia Militar"
    phone = Column(String, nullable=False)       # ex: "190"
    category = Column(String, nullable=True)     # ex: "segurança", "saúde"
    is_default = Column(Boolean, default=False)  # True = contato padrão do sistema
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at = Column(DateTime, nullable=True) # soft delete

    user = relationship("User", backref="emergency_contacts")