# Простая заглушка отчёта: bad / medium / good
from dataclasses import dataclass

def _ring_color(percent: int) -> str:
    if percent >= 80:
        return "#22c55e"  # emerald-500
    if percent >= 40:
        return "#f59e0b"  # amber-500
    return "#ef4444"      # rose/red-500

def make_report(case: str = "bad") -> dict:
    case = (case or "bad").lower()

    if case == "good":
        percent = 100
        violations = []
        footer = None
        flags = [
            {"type": "ok", "text": "Нет несоответствий ФЗ «О рекламе»", "strong": True},
            {"type": "ok", "text": "В соответствии с существующей судебной практикой риск привлечения к ответственности отсутствует", "strong": False},
            {"type": "ok", "text": "Шанс привлечения к ответственности мал", "strong": False},
        ]
        cases = [
            {
                "title": "Дело №022/05/18.1-1510/2023",
                "text": "Текст дела о рекламе",
                "fix": "Рекомендация от юристов"
            }
        ]
    elif case == "medium":
        percent = 80
        violations = [
            {
                "severity": "medium",
                "title": "Статья 5 пункт N",
                "text": "Текст статьи о нарушении. Описание сути выявленного несоответствия.",
                "fix": "Рекомендация от юристов по исправлению.",
                "link": "#"
            }
        ]
        footer = "Отображены <span class='text-rose-600'>не все</span> нарушения. Полный список доступен в PDF-отчёте."
        flags = [
            {"type": "ok", "text": "Нет несоответствий ФЗ «О рекламе»", "strong": False},
            {"type": "warn", "text": "В существующей судебной практике есть похожие случаи привлечения к ответственности", "strong": True},
            {"type": "ok", "text": "Шанс привлечения к ответственности мал", "strong": False},
        ]
        cases = [
            {
                "title": "Дело №022/05/18.1-1510/2023",
                "text": "Текст дела о рекламе",
                "fix": "Рекомендация от юристов"
            }
        ]
    else:
        # bad
        percent = 20
        violations = [
            {
                "severity": "critical",
                "title": "Статья 5 пункт 1",
                "text": "Запрещает использовать слова «лучший», «самый», «только», «абсолютный» и подобные.",
                "fix": "Добавить шкалу, по которой проводилась оценка, как сноску.",
                "link": "#"
            },
            {
                "severity": "critical",
                "title": "Статья 5 пункт 3",
                "text": "Запрещает указывать на лечебные свойства объекта рекламирования, если это не лекарственное средство, услуга или изделие.",
                "fix": "Убрать фразу, нарушающую статью, из рекламы.",
                "link": "#"
            },
            {
                "severity": "medium",
                "title": "Статья N пункт M",
                "text": "Текст статьи.",
                "fix": "Рекомендация от юристов.",
                "link": "#"
            },
            {
                "severity": "low",
                "title": "Статья N пункт M",
                "text": "Текст статьи.",
                "fix": "Рекомендация от юристов.",
                "link": "#"
            },
        ]
        footer = "Отображены <span class='text-rose-600'>не все</span> нарушения. Полный список нарушений доступен в PDF-отчёте."
        flags = [
            {"type": "warn", "text": "Есть несоответствия ФЗ «О рекламе»", "strong": True},
            {"type": "warn", "text": "В существующей судебной практике есть похожие случаи привлечения к ответственности", "strong": True},
            {"type": "warn", "text": "Есть шанс привлечения к ответственности", "strong": False},
        ]
        cases = [
            {
                "title": "Дело №022/05/18.1-1510/2023",
                "text": "В паблике ... распространялась рекламная информация без пометки «реклама».",
                "fix": "Добавить пометку «реклама» и регистрацию на ОРД."
            }
        ]

    ring_color = _ring_color(percent)
    ring_deg = float(percent) * 3.6

    return {
        "percent": percent,
        "ring_color": ring_color,
        "ring_deg": ring_deg,
        "violations": violations,
        "flags": flags,
        "cases": cases,
        "footer_note": footer,
    }
