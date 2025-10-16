"""
RQ Scheduler — планировщик задач для фоновых процессов.
Запускает парсер закона каждый день в 3:00 утра.
"""
from rq_scheduler import Scheduler
from datetime import datetime
from .queue import redis
from ..services.law_parser import parse_and_save_law


# Создаём scheduler с подключением к Redis
scheduler = Scheduler(connection=redis, queue_name="checks")


def setup_daily_tasks():
    """
    Настройка периодических задач.
    Вызывается при запуске worker'а.
    """
    # Очищаем старые задачи (чтобы не дублировались)
    for job in scheduler.get_jobs():
        if job.meta.get("task_name") == "daily_law_parsing":
            scheduler.cancel(job)
    
    # Парсинг закона каждый день в 3:00
    scheduler.cron(
        "0 3 * * *",  # cron: каждый день в 03:00
        func=parse_and_save_law,
        timeout="30m",  # таймаут 30 минут
        meta={"task_name": "daily_law_parsing"}
    )
    
    print("✅ Запланированы задачи:")
    print("  - Парсинг закона: каждый день в 03:00")


if __name__ == "__main__":
    """Запуск планировщика вручную для тестирования"""
    setup_daily_tasks()
    print("📅 Scheduler запущен. Нажмите Ctrl+C для остановки.")
    scheduler.run()

