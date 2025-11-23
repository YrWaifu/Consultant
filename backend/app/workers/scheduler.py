"""
RQ Scheduler — планировщик задач для фоновых процессов.
Запускает парсер закона каждый день в 3:00 утра.
"""
from datetime import datetime

from redis.exceptions import ReadOnlyError, RedisError
from rq_scheduler import Scheduler

from .queue import redis
from ..services.law_parser import parse_and_save_law


# Создаём scheduler с подключением к Redis
scheduler = Scheduler(connection=redis, queue_name="checks")


def setup_daily_tasks():
    """
    Настройка периодических задач.
    Вызывается при запуске worker'а.

    Важно: если Redis находится в режиме read-only (например, подключение
    идёт к реплике), мы НЕ падаем, а просто пропускаем настройку
    периодических задач, чтобы не уронить весь воркер.
    """
    try:
        # Очищаем старые задачи (чтобы не дублировались)
        for job in scheduler.get_jobs():
            # job.meta может быть пустым, поэтому подстрахуемся
            meta = getattr(job, "meta", {}) or {}
            if meta.get("task_name") == "daily_law_parsing":
                scheduler.cancel(job)

        # Парсинг закона каждый день в 3:00
        scheduler.cron(
            "0 3 * * *",  # cron: каждый день в 03:00
            func=parse_and_save_law,
            timeout="30m",  # таймаут 30 минут
            meta={"task_name": "daily_law_parsing"},
        )

        print("✅ Запланированы задачи:")
        print("  - Парсинг закона: каждый день в 03:00")

    except ReadOnlyError as e:
        # Типичный случай: подключились к read-only реплике Redis.
        # Не считаем это фатальной ошибкой для воркера.
        print(
            "⚠️ Redis в режиме read-only: периодические задачи не будут "
            "запланированы, но воркер продолжит работу. "
            f"Детали: {e}"
        )
    except RedisError as e:
        # Любые другие ошибки Redis при настройке задач — тоже не роняем воркер,
        # но логируем, чтобы можно было разобраться.
        print(
            "⚠️ Ошибка Redis при настройке периодических задач. "
            "Scheduler будет пропущен, воркер продолжит работу. "
            f"Детали: {e}"
        )
    except Exception as e:
        # Подстраховка от любых неожиданных ошибок, связанных с scheduler'ом.
        print(
            "⚠️ Не удалось настроить периодические задачи (нефатальная ошибка). "
            "Воркер продолжит работу без расписания. "
            f"Детали: {e}"
        )


if __name__ == "__main__":
    """Запуск планировщика вручную для тестирования"""
    setup_daily_tasks()
    print("📅 Scheduler запущен. Нажмите Ctrl+C для остановки.")
    scheduler.run()

