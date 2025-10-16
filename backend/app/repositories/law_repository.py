"""
Repository для работы с законами.
CRUD операции для LawVersion, LawChapter, LawArticle.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..models import LawVersion, LawChapter, LawArticle


class LawRepository:
    """Репозиторий для работы с законами"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== LawVersion ====================
    
    def get_active_version(self, law_code: str) -> Optional[LawVersion]:
        """Получить активную версию закона по коду"""
        return self.db.query(LawVersion).filter_by(
            law_code=law_code,
            is_active=True
        ).first()
    
    def get_version_by_id(self, version_id: int) -> Optional[LawVersion]:
        """Получить версию по ID"""
        return self.db.query(LawVersion).filter_by(id=version_id).first()
    
    def create_version(self, **kwargs) -> LawVersion:
        """Создать новую версию закона"""
        version = LawVersion(**kwargs)
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        return version
    
    def deactivate_versions(self, law_code: str) -> None:
        """Деактивировать все версии закона"""
        self.db.query(LawVersion).filter_by(
            law_code=law_code,
            is_active=True
        ).update({"is_active": False})
        self.db.commit()
    
    # ==================== LawChapter ====================
    
    def get_chapters_by_version(self, version_id: int) -> List[LawChapter]:
        """Получить все главы версии закона"""
        return self.db.query(LawChapter).filter_by(
            version_id=version_id
        ).order_by(LawChapter.chapter_number).all()
    
    def get_chapter_by_id(self, chapter_id: int) -> Optional[LawChapter]:
        """Получить главу по ID"""
        return self.db.query(LawChapter).filter_by(id=chapter_id).first()
    
    def create_chapter(self, **kwargs) -> LawChapter:
        """Создать главу"""
        chapter = LawChapter(**kwargs)
        self.db.add(chapter)
        self.db.commit()
        self.db.refresh(chapter)
        return chapter
    
    # ==================== LawArticle ====================
    
    def get_articles_by_version(self, version_id: int) -> List[LawArticle]:
        """Получить все статьи версии закона"""
        return self.db.query(LawArticle).filter_by(
            version_id=version_id
        ).all()
    
    def get_articles_by_chapter(self, chapter_id: int) -> List[LawArticle]:
        """Получить статьи главы"""
        return self.db.query(LawArticle).filter_by(
            chapter_id=chapter_id
        ).all()
    
    def get_article_by_number(self, version_id: int, article_number: str) -> Optional[LawArticle]:
        """Получить статью по номеру"""
        return self.db.query(LawArticle).filter_by(
            version_id=version_id,
            article_number=article_number
        ).first()
    
    def get_first_article(self, version_id: int) -> Optional[LawArticle]:
        """Получить первую статью"""
        return self.db.query(LawArticle).filter_by(
            version_id=version_id
        ).order_by(LawArticle.article_number).first()
    
    def search_articles(self, version_id: int, query: str, limit: int = 20) -> List[LawArticle]:
        """Поиск статей по тексту"""
        pattern = f"%{query.strip()}%"
        return self.db.query(LawArticle).filter(
            LawArticle.version_id == version_id,
            or_(
                LawArticle.title.ilike(pattern),
                LawArticle.content.ilike(pattern)
            )
        ).limit(limit).all()
    
    def create_article(self, **kwargs) -> LawArticle:
        """Создать статью"""
        article = LawArticle(**kwargs)
        self.db.add(article)
        return article
    
    def bulk_commit(self) -> None:
        """Закоммитить все изменения"""
        self.db.commit()

