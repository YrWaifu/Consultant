from dataclasses import dataclass
from datetime import datetime, date
from ..db import SessionLocal
from ..repositories.law_repository import LawRepository
from .ml_core import run_ml

def _ring_color(percent: int) -> str:
    if percent >= 80:
        return "#22c55e"  # emerald-500 (зеленый - хорошо)
    if percent > 20:
        return "#f59e0b"  # amber-500 (желтый - средне)
    return "#ef4444"      # rose/red-500 (красный - плохо)

def make_report_from_input(text: str | None, claims: list[str] | None = None, media_path: str | None = None) -> dict:
    """
    Генерация отчёта на основе реального вывода ML.
    text/claims/media_path — входные данные пользователя.
    """
    ml_out = run_ml(text, media_path)

    # Преобразуем вывод ML в структуру для шаблона
    violations: list[dict] = []
    cases: list[dict] = []

    for item in ml_out.get("text", []) or []:
        for article, info in item.items():
            # Пока все нарушения ссылаем на статью 5 ФЗ «О рекламе»
            law_article_id = "art-5"
            violations.append({
                "severity": "critical",  # базовая градация; можно доработать
                "title": str(article),
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

    # Итоговый процент и индикаторы
    has_violations = len(violations) > 0
    # Кольцо всегда полностью заполнено, цвет и подпись зависят от наличия нарушений
    percent = 100
    footer = None if not has_violations else ""
    flags = (
        [
            {"type": "ok", "text": "Нет несоответствий ФЗ «О рекламе»", "strong": True},
            {"type": "ok", "text": "В соответствии с существующей судебной практикой риск привлечения к ответственности отсутствует", "strong": False},
            {"type": "ok", "text": "Шанс привлечения к ответственности мал", "strong": False},
        ]
        if not has_violations
        else [
            {"type": "warn", "text": "Есть несоответствия ФЗ «О рекламе»", "strong": True},
            {"type": "warn", "text": "В существующей судебной практике есть похожие случаи привлечения к ответственности", "strong": True},
            {"type": "warn", "text": "Есть шанс привлечения к ответственности", "strong": False},
        ]
    )

    ring_color = "#ef4444" if has_violations else "#22c55e"
    ring_deg = 360.0
    ring_label = "Да" if has_violations else "Нет"

    # Дата проверки и информация о законе (из БД)
    check_date = datetime.now()

    # Получаем актуальную версию закона через репозиторий
    db = SessionLocal()
    repo = LawRepository(db)
    try:
        law_version = repo.get_active_version("38-FZ")

        if law_version:
            law_name = law_version.law_name
            law_version_date = law_version.version_date
        else:
            # Fallback если БД пустая
            law_name = "Федеральный закон от 13.03.2006 N 38-ФЗ «О рекламе»"
            law_version_date = date(2024, 10, 1)
    finally:
        db.close()

    return {
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
        # Юридическая информация
        "check_date": check_date,
        "law_name": law_name,
        "law_version_date": law_version_date,
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
