from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, JSON, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, date
from .db import Base
import enum


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    nickname = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    status = Column(String(32), default="active")  # active | expired | cancelled
    plan = Column(String(64), default="trial")  # trial | pro | enterprise
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    checks_quota = Column(Integer, default=100)  # месячный лимит проверок
    checks_used = Column(Integer, default=0)  # использовано в текущем месяце
    
    user = relationship("User", backref="subscription")


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


# ============ НОВЫЕ МОДЕЛИ ДЛЯ ЗАКОНА О РЕКЛАМЕ ============

class LawVersion(Base):
    """
    Версия закона на определённую дату.
    Каждый раз при парсинге создаётся новая версия.
    """
    __tablename__ = "law_versions"
    
    id = Column(Integer, primary_key=True)
    law_name = Column(String(512), nullable=False)  # "Федеральный закон от 13.03.2006 N 38-ФЗ «О рекламе»"
    law_code = Column(String(128), nullable=False)  # "38-FZ"
    source_url = Column(String(1024), nullable=False)  # URL на КонсультантПлюс
    version_date = Column(Date, nullable=False)  # Дата актуализации закона
    parsed_at = Column(DateTime, default=datetime.utcnow)  # Когда спарсили
    is_active = Column(Boolean, default=True)  # Активная версия (последняя)
    
    # Связь с статьями
    articles = relationship("LawArticle", back_populates="version", cascade="all, delete-orphan")
    chapters = relationship("LawChapter", back_populates="version", cascade="all, delete-orphan")


class LawChapter(Base):
    """
    Глава закона (структурная единица).
    """
    __tablename__ = "law_chapters"
    
    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey("law_versions.id"), nullable=False)
    chapter_number = Column(Integer, nullable=False)  # 1, 2, 3...
    title = Column(String(512), nullable=False)  # "Глава I. Общие положения"
    content = Column(Text)  # Полный текст главы
    source_url = Column(String(1024))
    
    version = relationship("LawVersion", back_populates="chapters")


class LawArticle(Base):
    """
    Статья закона (основная единица для проверки нарушений).
    """
    __tablename__ = "law_articles"
    
    id = Column(Integer, primary_key=True)
    version_id = Column(Integer, ForeignKey("law_versions.id"), nullable=False)
    chapter_id = Column(Integer, ForeignKey("law_chapters.id"), nullable=True)  # Принадлежность к главе
    article_number = Column(String(32), nullable=False)  # "5", "5.1", "20.1"
    title = Column(String(512), nullable=False)  # "Статья 5. Общие требования к рекламе"
    content = Column(Text, nullable=False)  # Текст статьи (plain text для поиска)
    content_html = Column(Text)  # HTML с форматированием (для отображения)
    summary = Column(Text)  # Краткое описание (для ML)
    source_url = Column(String(1024))
    
    # Для быстрого поиска нарушений
    keywords = Column(JSON)  # ["лучший", "самый", "превосходство"]
    violation_type = Column(String(128))  # "superlatives", "health_claims"
    
    version = relationship("LawVersion", back_populates="articles")
    chapter = relationship("LawChapter", backref="chapter_articles")