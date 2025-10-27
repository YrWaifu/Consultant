from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from .db import engine, SessionLocal, Base
from .models import Article, ArticleCategory
from .services.article_file_loader import ArticleFileLoader


def create_tables_if_not_exist():
    """Создает таблицы статей, если они не существуют"""
    try:
        # Проверяем существование таблиц
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # Проверяем наличие таблиц статей
        articles_table_exists = 'articles' in tables
        categories_table_exists = 'article_categories' in tables

        if not articles_table_exists or not categories_table_exists:
            print("🔧 Создаем таблицы статей...")
            
            # Создаем только таблицы статей
            ArticleCategory.__table__.create(engine, checkfirst=True)
            Article.__table__.create(engine, checkfirst=True)
            
            print("✅ Таблицы статей созданы")
            return True
        else:
            print("✅ Таблицы статей уже существуют")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        return False


def check_and_init_articles():
    """Проверяет существование таблиц статей и заполняет их примерами данных при необходимости"""
    try:
        # Сначала пытаемся создать таблицы, если их нет
        tables_created = create_tables_if_not_exist()
        
        if not tables_created:
            print("⚠️  Не удалось создать таблицы статей")
            return False
        
        # Проверяем наличие данных в таблицах
        db = SessionLocal()
        try:
            categories_count = db.query(ArticleCategory).count()
            articles_count = db.query(Article).count()
            
            print(f"📊 Статистика статей: {categories_count} категорий, {articles_count} статей")
            
            # Если нет данных, создаем примеры
            if categories_count == 0 or articles_count == 0:
                print("📝 Данные статей отсутствуют. Загружаем...")

                from pathlib import Path
                ARTICLES_DIR = str(Path(__file__).resolve().parents[2] / "articles")

                article_loader=ArticleFileLoader()
                result = article_loader.load_from_markdown_directory(ARTICLES_DIR)
                
                print(f"✅ Создано {result['categories_created']} категорий и {result['articles_created']} статей")
                return True
            else:
                print("✅ Данные статей уже существуют")
                return True
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Ошибка при проверке статей: {e}")
        return False
