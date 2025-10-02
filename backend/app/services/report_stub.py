# Простая заглушка отчёта: bad / medium / good
from dataclasses import dataclass

def _ring_color(percent: int) -> str:
    if percent >= 80:
        return "#22c55e"  # emerald-500 (зеленый - хорошо)
    if percent > 20:
        return "#f59e0b"  # amber-500 (желтый - средне)
    return "#ef4444"      # rose/red-500 (красный - плохо)

def make_report(case: str = "bad") -> dict:
    case = (case or "bad").lower()

    if case == "good":
        percent = 100
        violations = []
        marked_violations = []
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
        percent = 75
        violations = [
            {
                "severity": "medium",
                "title": "Статья 5 пункт N",
                "text": "Текст статьи о нарушении. Описание сути выявленного несоответствия.",
                "fix": "Рекомендация от юристов по исправлению.",
                "link": "#"
            }
        ]
        marked_violations = []
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
        ]
        marked_violations = [
            {
                "severity": "medium",
                "title": "Статья N пункт M",
                "text": "Текст статьи",
                "fix": "Рекомендация от юристов",
                "link": "#"
            },
            {
                "severity": "low",
                "title": "Статья N пункт M",
                "text": "Текст статьи",
                "fix": "Рекомендация от юристов",
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
        "marked_violations": marked_violations,
        "flags": flags,
        "cases": cases,
        "footer_note": footer,
    }


def make_report_pdf_bytes(case: str = "bad") -> bytes:
    """
    Генерирует простой PDF-заглушку в байтах для скачивания.
    Чтобы не тянуть зависимости, создаём минимальный PDF руками.
    """
    title = f"Отчёт по проверке — {case.upper()}"
    # Простейший одностраничный PDF (A4), текст в центре.
    # Источник структуры: минимальный синтетический PDF без внешних пакетов.
    content_text = f"BT /F1 24 Tf 100 700 Td ({title}) Tj ET"
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        + f"4 0 obj << /Length {len(content_text)} >> stream\n".encode("utf-8") + content_text.encode("utf-8") + b"\nendstream endobj\n"
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n"
    )
    startxref = len(pdf)
    pdf += str(startxref).encode("ascii") + b"\n%%EOF"
    return pdf
