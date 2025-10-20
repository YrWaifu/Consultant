from rq import Queue
from redis import Redis
from ..settings import settings


redis = Redis.from_url(settings.REDIS_URL)
queue = Queue("checks", connection=redis)

# Фоновая задача для обработки ML модели
def process_ad_check_task(text: str | None, media_path: str | None):
    """
    Фоновая задача для обработки проверки рекламы через ML модель.
    Выполняется в отдельном процессе воркера.
    """
    print(f"🚀 Начинаем обработку ML задачи. Текст: {text[:100] if text else 'None'}...")
    
    try:
        from ..services.ml_core import run_ml
        from ..repositories.law_repository import LawRepository  
        from ..db import SessionLocal
        from datetime import datetime, date
        
        print("📚 Запускаем ML обработку...")
        # Запускаем ML обработку
        ml_out = run_ml(text, media_path)
        print(f"✅ ML обработка завершена! Результат: {ml_out}")
        
    except Exception as e:
        print(f"❌ Ошибка в ML обработке: {e}")
        import traceback
        print(f"📜 Полный трейс: {traceback.format_exc()}")
        # Пробрасываем ошибку дальше
        raise e
    
    print("🔧 Обрабатываем результат ML в структуру отчета...")
    try:
        # Преобразуем вывод ML в структуру для отчета
        violations: list[dict] = []
        cases: list[dict] = []

        def format_violation_title(article_str):
            """Преобразует 'Часть X. Пункт Y' в 'п.Y ч.X ст.5 ФЗ о рекламе'"""
            import re
            
            # Парсим строку типа "Часть 5. Пункт 1"
            match = re.match(r'Часть (\d+(?:\.\d+)?)\. Пункт (\d+)', article_str)
            if match:
                part = match.group(1)
                point = match.group(2)
                return f"п.{point} ч.{part} ст.5 ФЗ о рекламе"
            
            # Парсим строки типа "Часть 6" (без пункта)
            match = re.match(r'Часть (\d+(?:\.\d+)?)$', article_str)
            if match:
                part = match.group(1)
                return f"ч.{part} ст.5 ФЗ о рекламе"
            
            # Парсим строки типа "Части 10.1 и 10.2"
            if "Части" in article_str and "и" in article_str:
                return f"{article_str} ст.5 ФЗ о рекламе"
            
            # Если не удалось распарсить, возвращаем исходную строку
            return article_str
        
        for item in ml_out.get("text", []) or []:
            for article, info in item.items():
                law_article_id = "art-5"
                formatted_title = format_violation_title(str(article))
                violations.append({
                    "severity": "critical",
                    "title": formatted_title,
                    "text": info.get("text") or "",
                    "fix": info.get("recommendations") or "",
                    "link": f"/v2/laws/article/{law_article_id}",
                })
                jp = info.get("judicial_proceedings") or {}
                for case_title, case_text in jp.items():
                    cases.append({
                        "title": case_title,
                        "text": case_text,
                        "fix": info.get("recommendations") or "",
                    })

        print(f"📊 Найдено нарушений: {len(violations)}, кейсов: {len(cases)}")

        # Формируем результат
        has_violations = len(violations) > 0
        percent = 100
        footer = None if not has_violations else ""
        # Формируем текст с количеством нарушений
        violations_count = len(violations)
        if violations_count == 1:
            violations_text = f"Выявлено {violations_count} несоответствие ФЗ «О рекламе»"
        elif 2 <= violations_count <= 4:
            violations_text = f"Выявлено {violations_count} несоответствия ФЗ «О рекламе»"
        else:
            violations_text = f"Выявлено {violations_count} несоответствий ФЗ «О рекламе»"
        
        flags = (
            [
                {"type": "ok", "text": "Нет несоответствий ФЗ «О рекламе»", "strong": True},
                {"type": "ok", "text": "В соответствии с существующей судебной практикой риск привлечения к ответственности отсутствует", "strong": False},
                {"type": "ok", "text": "Риск привлечения к ответственности мал", "strong": False},
            ]
            if not has_violations
            else [
                {"type": "warn", "text": violations_text, "strong": True},
                {"type": "warn", "text": "В существующей судебной практике есть похожие случаи привлечения к ответственности", "strong": True},
                {"type": "warn", "text": "Есть риск привлечения к ответственности", "strong": False},
            ]
        )

        ring_color = "#ef4444" if has_violations else "#22c55e"
        ring_deg = 360.0
        ring_label = "Нет" if has_violations else "Да" 
        check_date = datetime.now()

        print("🗃️ Получаем информацию о законе из БД...")
        # Получаем информацию о законе
        db = SessionLocal()
        repo = LawRepository(db)
        try:
            law_version = repo.get_active_version("38-FZ")
            if law_version:
                law_name = law_version.law_name
                law_version_date = law_version.version_date
            else:
                law_name = "Федеральный закон \"О рекламе\" от 13.03.2006 N 38-ФЗ (последняя редакция)"
                law_version_date = date(2024, 10, 1)
        finally:
            db.close()

        # Форматируем даты для JSON совместимости
        check_date_str = check_date.strftime('%d.%m.%Y в %H:%M')
        check_date_short = check_date.strftime('%d.%m.%Y')
        
        result = {
            "percent": percent,
            "ring_color": ring_color,
            "ring_deg": ring_deg,
            "ring_label": ring_label,
            "is_ok": (not has_violations),
            "violations": violations,
            "marked_violations": [],
            "flags": flags,
            "cases": cases,
            "footer_note": footer,
            "check_date_formatted": check_date_str,  # Уже отформатированная дата
            "check_date_short": check_date_short,    # Короткая версия для статуса
            "law_name": law_name,
            "law_version_date": law_version_date.isoformat() if hasattr(law_version_date, 'isoformat') else str(law_version_date),
            "input_text": text,  # Исходный текст рекламы
        }
        
        print("🎉 Отчет сформирован успешно!")
        print(f"🔍 Типы данных в результате: {[(k, type(v).__name__) for k, v in result.items()]}")
        return result
        
    except Exception as e:
        print(f"❌ Ошибка при формировании отчета: {e}")
        import traceback
        print(f"📜 Полный трейс: {traceback.format_exc()}")
        # Пробрасываем ошибку дальше
        raise e

