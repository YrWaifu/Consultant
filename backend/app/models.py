from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, JSON, Enum, Boolean
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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    status = Column(String(32), default="active")  # active | expired | cancelled
    plan = Column(String(64), default="trial")  # trial | pro | enterprise
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    checks_quota = Column(Integer, default=5)  # лимит проверок (5 для trial, 20 для pro)
    checks_used = Column(Integer, default=0)  # использовано
    last_reset_at = Column(DateTime, default=datetime.utcnow)  # последний сброс счетчика (для недельного обновления)
    
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


# ============ МОДЕЛИ ДЛЯ СТАТЕЙ ============

class ArticleCategory(Base):
    """
    Категории статей (например, "Нужно знать при проверке рекламы", "Обзоры от юристов", "Интересные кейсы")
    """
    __tablename__ = "article_categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)  # "Нужно знать при проверке рекламы"
    slug = Column(String(255), nullable=False, unique=True)  # "ad-check-knowledge"
    description = Column(Text)  # Описание категории
    icon = Column(String(100))  # Иконка для отображения (например, "📌")
    sort_order = Column(Integer, default=0)  # Порядок сортировки

    # Связь со статьями
    articles = relationship("Article", back_populates="category", cascade="all, delete-orphan")


class Article(Base):
    """
    Статьи для раздела "Полезные статьи"
    """
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("article_categories.id"), nullable=False)
    title = Column(String(512), nullable=False)  # Заголовок статьи
    slug = Column(String(512), nullable=False, unique=True)  # URL-слаг
    excerpt = Column(Text)  # Краткое описание
    content = Column(Text, nullable=False)  # Полный текст статьи

    created_at = Column(DateTime, default=datetime.utcnow)  # Дата создания
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Дата обновления

    sort_order = Column(Integer, default=0)  # Порядок сортировки в категории
    view_count = Column(Integer, default=0)  # Количество просмотров
    
    # Связь с категорией
    category = relationship("ArticleCategory", back_populates="articles")