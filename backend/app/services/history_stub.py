from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Dict


def _mk_item(title: str, days_ago: int, result: str, report_url: str | None = None, pdf_url: str | None = None) -> Dict:
    dt = datetime.now() - timedelta(days=days_ago)
    if result == "ok":
        badge_class, badge_text = "bg-green-100 text-green-700", "OK"
    elif result == "warn":
        badge_class, badge_text = "bg-amber-100 text-amber-700", "Есть замечания"
    else:
        badge_class, badge_text = "bg-rose-100 text-rose-700", "Нарушения"
    return {
        "date": dt.strftime("%Y-%m-%d %H:%M"),
        "title": title,
        "summary": None,
        "badge_class": badge_class,
        "badge_text": badge_text,
        "report_url": report_url,
        "pdf_url": pdf_url,
    }


def list_history() -> List[Dict]:
    """Заглушка истории проверок для демо UI."""
    return [
        _mk_item("Промо‑пост про скидки", 1, "bad", "/v2/report?case=bad", "/v2/report.pdf?case=bad"),
        _mk_item("Текст баннера для сайта", 3, "warn", "/v2/report?case=medium", "/v2/report.pdf?case=medium"),
        _mk_item("Анонс вебинара", 10, "ok", "/v2/report?case=good", "/v2/report.pdf?case=good"),
    ]


