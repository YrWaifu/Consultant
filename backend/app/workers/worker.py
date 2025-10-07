from rq import Worker
from .queue import redis  # это экземпляр Redis с твоего REDIS_URL
from .scheduler import setup_daily_tasks
from ..services.law_parser import parse_and_save_law
from ..models import LawVersion
from ..db import SessionLocal

if __name__ == "__main__":
    print("🔧 Настройка планировщика задач...")
    setup_daily_tasks()
    
    # Проверяем, есть ли данные в БД, если нет - запускаем парсер
    print("🔍 Проверка наличия закона в БД...")
    import time
    
    # Retry: ждем готовности БД (до 30 сек)
    for attempt in range(10):
        try:
            db = SessionLocal()
            law_exists = db.query(LawVersion).filter_by(law_code="38-FZ", is_active=True).first()
            
            if not law_exists:
                print("📚 Закон не найден в БД, запускаю первичный парсинг...")
                parse_and_save_law()
                print("✅ Первичный парсинг завершён!")
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
    
    print("🚀 Запуск RQ Worker...")
    Worker(["checks"], connection=redis).work(with_scheduler=True)