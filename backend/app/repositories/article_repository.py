from sqlalchemy.orm import Session
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional
from ..db import SessionLocal
from ..models import Article, ArticleCategory


class ArticleRepository:
    def __init__(self, db: Session):
        self.db: Session = db

    def get_categories(self) -> List[ArticleCategory]:
        """Получить все активные категории статей"""
        return self.db.query(ArticleCategory)\
            .filter(ArticleCategory.is_active == True)\
            .order_by(ArticleCategory.sort_order, ArticleCategory.name)\
            .all()

    def get_category_by_slug(self, slug: str) -> Optional[ArticleCategory]:
        """Получить категорию по слагу"""
        return self.db.query(ArticleCategory)\
            .filter(ArticleCategory.slug == slug, ArticleCategory.is_active == True)\
            .first()

    def get_articles_by_category(self, category_slug: str, limit: int = None) -> List[Article]:
        """Получить статьи по категории"""
        query = self.db.query(Article)\
            .join(ArticleCategory)\
            .filter(
                ArticleCategory.slug == category_slug,
                Article.is_published == True,
                ArticleCategory.is_active == True
            )\
            .order_by(Article.sort_order, desc(Article.published_at))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()

    def get_article_by_slug(self, slug: str) -> Optional[Article]:
        """Получить статью по слагу"""
        return self.db.query(Article)\
            .join(ArticleCategory)\
            .filter(
                Article.slug == slug,
                Article.is_published == True,
                ArticleCategory.is_active == True
            )\
            .first()

    def article_exists_by_slug(self, slug: str) -> bool:
        """Проверить существование статьи по слагу (включая неопубликованные)"""
        return self.db.query(Article).filter(Article.slug == slug).first() is not None

    def get_latest_articles(self, limit: int = 10) -> List[Article]:
        """Получить последние статьи"""
        return self.db.query(Article)\
            .join(ArticleCategory)\
            .filter(
                Article.is_published == True,
                ArticleCategory.is_active == True
            )\
            .order_by(desc(Article.published_at))\
            .limit(limit)\
            .all()

    def search_articles(self, query: str) -> List[Article]:
        """Поиск статей по тексту"""
        search_term = f"%{query.lower()}%"
        return self.db.query(Article)\
            .join(ArticleCategory)\
            .filter(
                Article.is_published == True,
                ArticleCategory.is_active == True,
                (
                    Article.title.ilike(search_term) |
                    Article.excerpt.ilike(search_term) |
                    Article.content.ilike(search_term)
                )
            )\
            .order_by(desc(Article.published_at))\
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
                      content: str, excerpt: str = None, author: str = None,
                      content_html: str = None, sort_order: int = 0) -> Article:
        """Создать новую статью"""
        article = Article(
            category_id=category_id,
            title=title,
            slug=slug,
            content=content,
            excerpt=excerpt,
            author=author,
            content_html=content_html,
            sort_order=sort_order
        )
        print(article)
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        return article
