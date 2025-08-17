from datetime import datetime
import enum

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date,
    ForeignKey, CheckConstraint, func
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Enum as SqlEnum

from app.database import Base


# ---------- Pessoas ----------

# app/models.py (trecho)
class Pessoa(Base):
    __tablename__ = "pessoas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)  
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    deleted_at = Column(DateTime, nullable=True)



# ---------- Check-ins ----------

class CheckInType(str, enum.Enum):
    alegria = "alegria"
    tristeza = "tristeza"
    angustia = "angustia"
    magoa = "mágoa"
    ansiedade = "ansiedade"

class CheckIn(Base):
    __tablename__ = "check_ins"

    id = Column(Integer, primary_key=True, index=True)
    pessoa_id = Column(Integer, ForeignKey("pessoas.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    checkin_type = Column(SqlEnum(CheckInType, name="moodtype"), nullable=False)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("score >= 1 AND score <= 5", name="ck_check_ins_score_range"),
    )

    pessoa = relationship("Pessoa", backref=backref("check_ins", cascade="all, delete-orphan"))


# ---------- Lembretes ----------
class Lembrete(Base):
    __tablename__ = "lembretes"

    id = Column(Integer, primary_key=True, index=True)
    pessoa_id = Column(Integer, ForeignKey("pessoas.id", ondelete="CASCADE"), nullable=False, index=True)
    message = Column(String, nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=False)
    done = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    pessoa = relationship("Pessoa", backref=backref("lembretes", cascade="all, delete-orphan"))


# ---------- Contatos de Emergência ----------
class ContatoEmergencia(Base):
    __tablename__ = "contatos_emergencia"

    id = Column(Integer, primary_key=True, index=True)
    pessoa_id = Column(Integer, ForeignKey("pessoas.id", ondelete="CASCADE"), nullable=True, index=True)

    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    category = Column(String, nullable=True)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    pessoa = relationship("Pessoa", backref="contatos_emergencia")
