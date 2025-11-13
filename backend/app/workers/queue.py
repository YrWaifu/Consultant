from rq import Queue
from redis import Redis
from ..settings import settings
import os


redis = Redis.from_url(settings.REDIS_URL)
queue = Queue("checks", connection=redis)

# Фоновая задача для обработки ML модели
def process_ad_check_task(text: str | None, audio_bytes: bytes | None, audio_content_type: str | None, check_id: str | None = None):
    """
    Фоновая задача для обработки проверки рекламы через ML модель.
    Выполняется в отдельном процессе воркера.
    """
    print(f"🚀 Начинаем обработку ML задачи. Текст: {text[:100] if text else 'None'}...")
    print(f"🎵 Аудио: {'есть' if audio_bytes else 'нет'}, тип: {audio_content_type}")

    try:
        from ..services.ml_core import run_ml
        from ..repositories.law_repository import LawRepository  
        from ..db import SessionLocal
        from datetime import datetime, date
        
        print("📚 Запускаем ML обработку...")
        # Запускаем ML обработку
        ml_out = run_ml(text, audio_bytes, audio_content_type)
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
            """Преобразует 'Часть X. Пункт Y' в 'п.Y ч.X ст.5 ФЗ "О рекламе" N 38-ФЗ'"""
            import re
            
            # Парсим строку типа "Часть 5. Пункт 1"
            match = re.match(r'Часть (\d+(?:\.\d+)?)\. Пункт (\d+)', article_str)
            if match:
                part = match.group(1)
                point = match.group(2)
                return f"п.{point} ч.{part} ст.5 ФЗ \"О рекламе\" N 38-ФЗ"
            
            # Парсим строки типа "Часть 6" (без пункта)
            match = re.match(r'Часть (\d+(?:\.\d+)?)$', article_str)
            if match:
                part = match.group(1)
                return f"ч.{part} ст.5 ФЗ \"О рекламе\" N 38-ФЗ"
            
            # Парсим строки типа "Части 10.1 и 10.2"
            if "Части" in article_str and "и" in article_str:
                return f"{article_str} ст.5 ФЗ \"О рекламе\" N 38-ФЗ"
            
            # Обрабатываем случай, когда в строке есть просто "ст. 5" или "ст.5" без "ФЗ"
            if re.search(r'ст\.\s*5\b', article_str, re.IGNORECASE) and 'ФЗ' not in article_str:
                # Заменяем "ст. 5" или "ст.5" на "ст. 5 ФЗ "О рекламе" N 38-ФЗ"
                result = re.sub(r'ст\.\s*5\b', 'ст.5 ФЗ "О рекламе" N 38-ФЗ', article_str, flags=re.IGNORECASE)
                return result
            
            # Если не удалось распарсить, возвращаем исходную строку
            return article_str
        
        for item in ml_out.get("text", []) or []:
            for article, info in item.items():
                law_article_id = "art-5"
                formatted_title = format_violation_title(str(article))
                
                # Собираем случаи для этого нарушения
                violation_cases = []
                jp = info.get("judicial_proceedings") or {}
                for case_title, case_text in jp.items():
                    violation_cases.append({
                        "title": case_title,
                        "text": case_text,
                        "fix": info.get("recommendations") or "",
                    })
                    # Также добавляем в общий список для обратной совместимости
                    cases.append({
                        "title": case_title,
                        "text": case_text,
                        "fix": info.get("recommendations") or "",
                    })
                
                violations.append({
                    "severity": "critical",
                    "title": formatted_title,
                    "text": info.get("text") or "",
                    "fix": info.get("recommendations") or "",
                    "link": f"/v2/laws/article/{law_article_id}",
                    "cases": violation_cases,  # Добавляем случаи в нарушение
                })

        print(f"📊 Найдено нарушений: {len(violations)}, кейсов: {len(cases)}")

        # Формируем результат
        has_violations = len(violations) > 0
        percent = 100
        footer = None if not has_violations else ""
        # Формируем текст с количеством нарушений
        violations_count = len(violations)
        if violations_count == 1:
            violations_text = f"Выявлено {violations_count} несоответствие ФЗ «О рекламе» N 38-ФЗ"
        elif 2 <= violations_count <= 4:
            violations_text = f"Выявлено {violations_count} несоответствия ФЗ «О рекламе» N 38-ФЗ"
        else:
            violations_text = f"Выявлено {violations_count} несоответствий ФЗ «О рекламе» N 38-ФЗ"
        
        flags = (
            [
                {"type": "ok", "text": "Нет несоответствий ФЗ «О рекламе»", "strong": True},
                {"type": "ok", "text": "Риск привлечения к ответственности мал", "strong": False},
                {"type": "ok", "text": "В существующей судебной практике похожие случаи отсутствуют", "strong": False},
            ]
            if not has_violations
            else [
                {"type": "warn", "text": violations_text, "strong": True},
                {"type": "warn", "text": "Есть риск привлечения к ответственности", "strong": False},
                {"type": "warn", "text": "В существующей судебной практике есть похожие случаи", "strong": True},
            ]
        )

        ring_color = "#ef4444" if has_violations else "#22c55e"
        ring_deg = 360.0
        ring_label = "Нет" if has_violations else "Да" 
        check_date = datetime.now()

        print("🗃️ Получаем информацию о законе из БД...")
        # Получаем информацию о законе
        from ..services.law_parser import fetch_law_name
        db = SessionLocal()
        repo = LawRepository(db)
        try:
            law_version = repo.get_active_version("38-FZ")
            if law_version:
                # Используем fetch_law_name() для получения актуального названия, как на странице ФЗ
                law_name = fetch_law_name()
                law_version_date = law_version.version_date
            else:
                law_name = fetch_law_name()
                law_version_date = date(2024, 10, 1)
        finally:
            db.close()

        # Форматируем даты для JSON совместимости
        check_date_str = check_date.strftime('%d.%m.%Y в %H:%M')
        check_date_short = check_date.strftime('%d.%m.%Y')
        
        # Получаем текст для отображения: либо исходный текст, либо распознанный из аудио
        display_text = text
        is_audio = False
        if not text and audio_bytes:
            # Если был загружен аудио файл, используем распознанный текст
            display_text = ml_out.get("recognized_text")
            is_audio = True
        
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
            "input_text": display_text,  # Исходный текст рекламы или распознанный из аудио
            "is_audio": is_audio,  # Флаг, указывающий, что это аудио реклама
        }
        
        print("🎉 Отчет сформирован успешно!")
        print(f"🔍 Типы данных в результате: {[(k, type(v).__name__) for k, v in result.items()]}")

        # Сохраняем результат в БД если передан check_id
        if check_id:
            try:
                from ..repositories.check_repository import CheckRepository
                db = SessionLocal()
                check_repo = CheckRepository(db)

                # Формируем краткую сводку
                violations_count = len(result.get('violations', []))
                if result['is_ok']:
                    summary = "✅ Соответствует законодательству"
                else:
                    # Правильное склонение слова "несоответствие"
                    if violations_count % 10 == 1 and violations_count % 100 != 11:
                        word = "несоответствие"
                    elif violations_count % 10 in [2, 3, 4] and violations_count % 100 not in [12, 13, 14]:
                        word = "несоответствия"
                    else:
                        word = "несоответствий"
                    summary = f"⚠️ Обнаружено {violations_count} {word}"

                # Сохраняем результат
                check_repo.update_result(
                    check_id=check_id,
                    summary=summary,
                    result=result,
                    status="done"
                )
                print(f"💾 Результат сохранен в БД (check_id={check_id})")
                db.close()
            except Exception as save_error:
                print(f"⚠️ Ошибка при сохранении в БД: {save_error}")
                # Не пробрасываем ошибку дальше, т.к. результат все равно вернется

        return result
        
    except Exception as e:
        print(f"❌ Ошибка при формировании отчета: {e}")
        import traceback
        print(f"📜 Полный трейс: {traceback.format_exc()}")
        # Пробрасываем ошибку дальше
        raise e


# Фоновая задача для инициализации статей

def init_articles_task():
    print("🔍 Запуск заливки статей в БД...")
    from backend.app.init_articles import check_and_init_articles
    result = check_and_init_articles()
    print(f"✅ Итог заливки статей: {result}")
    return result
