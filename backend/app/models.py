from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base
import enum


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="user")


class Check(Base):
    __tablename__ = "checks"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    input_text = Column(Text)
    input_media_path = Column(String(512))
    status = Column(String(32), default="queued") # queued|running|done|failed
    summary = Column(Text) # короткий вывод
    result = Column(JSON) # полные метрики/нарушения


user = relationship("User")


class LawSnippet(Base):
    __tablename__ = "law_snippets"
    id = Column(Integer, primary_key=True)
    law_code = Column(String(128)) # напр. "38-ФЗ"
    title = Column(String(512))
    text = Column(Text)
    meta = Column(JSON)