from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, Type
from datetime import datetime
from ..models import Article, ArticleCategory


class ArticleRepository:
    def __init__(self, db: Session):
        self.db: Session = db

    def get_categories(self) -> list[Type[ArticleCategory]]:
        """Получить все активные категории статей"""
        return self.db.query(ArticleCategory) \
            .order_by(ArticleCategory.sort_order, ArticleCategory.name) \
            .all()

    def get_category_by_slug(self, slug: str) -> Optional[ArticleCategory]:
        """Получить категорию по слагу"""
        return self.db.query(ArticleCategory) \
            .filter(ArticleCategory.slug == slug) \
            .first()

    def get_articles_by_category(self, category_slug: str, limit: int = None) -> list[Type[Article]]:
        """Получить статьи по категории"""
        query = self.db.query(Article) \
            .join(ArticleCategory) \
            .filter(
            ArticleCategory.slug == category_slug
        ) \
            .order_by(Article.sort_order, desc(Article.created_at))

        if limit:
            query = query.limit(limit)

        return query.all()

    def get_article_by_slug(self, slug: str) -> Optional[Article]:
        """Получить статью по слагу"""
        return self.db.query(Article) \
            .join(ArticleCategory) \
            .filter(
            Article.slug == slug
        ) \
            .first()

    def article_exists_by_slug(self, slug: str) -> bool:
        """Проверить существование статьи по слагу (включая неопубликованные)"""
        return self.db.query(Article).filter(Article.slug == slug).first() is not None

    def get_latest_articles(self, limit: int = 10) -> list[Type[Article]]:
        """Получить последние статьи"""
        return self.db.query(Article) \
            .join(ArticleCategory) \
            .order_by(desc(Article.created_at)) \
            .limit(limit) \
            .all()

    def search_articles(self, query: str) -> list[Type[Article]]:
        """Поиск статей по тексту"""
        search_term = f"%{query.lower()}%"
        return self.db.query(Article) \
            .join(ArticleCategory) \
            .filter(

            Article.title.ilike(search_term) |
            Article.excerpt.ilike(search_term) |
            Article.content.ilike(search_term)

        ) \
            .order_by(desc(Article.created_at)) \
            .all()

    def increment_view_count(self, article_id: int):
        """Увеличить счетчик просмотров"""
        article = self.db.query(Article).filter(Article.id == article_id).first()
        if article:
            article.view_count += 1
            self.db.commit()

    def create_category(self, name: str, slug: str, description: str = None,
                        icon: str = None, sort_order: int = 0) -> ArticleCategory:
        """Создать новую категорию"""
        category = ArticleCategory(
            name=name,
            slug=slug,
            description=description,
            icon=icon,
            sort_order=sort_order
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def create_article(self, category_id: int, title: str, slug: str,
                       content: str, excerpt: str = None,
                       sort_order: int = 0, created_at: datetime = datetime.utcnow()) -> Article:
        """Создать новую статью"""
        article = Article(
            category_id=category_id,
            title=title,
            slug=slug,
            content=content,
            excerpt=excerpt,
            created_at=created_at,
            sort_order=sort_order
        )
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        return article
