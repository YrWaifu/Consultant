from rq import Worker
from .queue import redis  # это экземпляр Redis с твоего REDIS_URL
from .scheduler import setup_daily_tasks
from ..services.law_parser import parse_and_save_law
from ..db import SessionLocal
from ..repositories.law_repository import LawRepository
from .queue import init_articles_task
from ..models import Article, ArticleCategory

if __name__ == "__main__":
    print("🔧 Настройка планировщика задач...")
    setup_daily_tasks()
    
    # Проверяем, есть ли данные в БД, если нет - добавляем задачу парсинга в очередь
    print("🔍 Проверка наличия закона в БД...")
    import time
    from .queue import queue
    
    # Retry: ждем готовности БД (до 30 сек)
    for attempt in range(10):
        try:
            db = SessionLocal()
            repo = LawRepository(db)
            law_exists = repo.get_active_version("38-FZ")
            
            if not law_exists:
                print("📚 Закон не найден в БД, добавляю задачу парсинга в очередь...")
                # Добавляем задачу в очередь вместо синхронного выполнения
                queue.enqueue(parse_and_save_law, job_timeout='30m')
                print("✅ Задача парсинга добавлена в очередь!")
            else:
                print(f"✅ Закон найден в БД (версия от {law_exists.version_date})")
            
            db.close()
            break  # Успешно - выходим
            
        except Exception as e:
            if attempt < 9:
                print(f"⏳ БД не готова, повтор через 3 сек... ({attempt + 1}/10)")
                time.sleep(3)
            else:
                print(f"⚠️ Не удалось подключиться к БД: {e}")
                break
    
    # Проверяем, есть ли статьи/категории в БД, если нет - добавляем задачу заливки статей
    print("🔍 Проверка наличия статей и категорий в БД...")
    from ..db import SessionLocal
    from ..models import Article, ArticleCategory
    # Повторяем проверку также с ретраями, как для закона
    for attempt in range(10):
        try:
            db = SessionLocal()
            cats = db.query(ArticleCategory).count()
            arts = db.query(Article).count()
            if cats == 0 or arts == 0:
                print("📚 Нет статей/категорий в БД, добавляю задачу заполнения в очередь...")
                queue.enqueue(init_articles_task, job_timeout='10m')
                print("✅ Задача добавления статей поставлена в очередь!")
            else:
                print(f"✅ В базе уже есть {cats} категорий и {arts} статей.")
            db.close()
            break
        except Exception as e:
            if attempt < 9:
                print(f"⏳ БД не готова, повтор через 3 сек... ({attempt + 1}/10)")
                time.sleep(3)
            else:
                print(f"⚠️ Не удалось подключиться к БД (init_articles): {e}")
                break
    
    print("🚀 Запуск RQ Worker...")
    Worker(["checks"], connection=redis).work(with_scheduler=True)