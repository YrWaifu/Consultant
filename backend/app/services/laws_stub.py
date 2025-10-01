from __future__ import annotations

# Простейшая модель данных для заглушки
LAW_TITLE = 'Федеральный закон «О рекламе»'
LAW_META = 'от 13.03.2006 N 38-ФЗ'

_TOC = [
    {
        "chapter": "Глава 1. Общие положения",
        "items": [
            {"id": "ch1-art1", "title": "Статья 1. Цели настоящего Федерального закона"},
            {"id": "ch1-art2", "title": "Статья 2. Сфера применения настоящего Федерального закона"},
            {"id": "ch1-art3", "title": "Статья 3. Термины и определения"},
            {"id": "ch1-art4", "title": "Статья 4. Требования к рекламе"},
        ],
    },
    {
        "chapter": "Глава 2. Общие положения",
        "items": [
            {"id": "ch2-art1", "title": "Статья 1. Цели"},
            {"id": "ch2-art2", "title": "Статья 2. Сфера применения"},
            {"id": "ch2-art3", "title": "Статья 3. Текст"},
            {"id": "ch2-art4", "title": "Статья 4. Текст"},
        ],
    },
    {
        "chapter": "Глава 3. Общие положения",
        "items": [
            {"id": "ch3-art1", "title": "Статья 1. Цели"},
            {"id": "ch3-art2", "title": "Статья 2. Сфера применения"},
            {"id": "ch3-art3", "title": "Статья 3. Текст"},
            {"id": "ch3-art4", "title": "Статья 4. Текст"},
        ],
    },
]


def get_law_index() -> dict:
    """Список разделов/статей закона."""
    return {"title": LAW_TITLE, "meta": LAW_META, "toc": _TOC}


def _flat_ids():
    return [it["id"] for ch in _TOC for it in ch["items"]]


def _find_article(article_id: str):
    for ch in _TOC:
        for it in ch["items"]:
            if it["id"] == article_id:
                return ch["chapter"], it
    return None, None


def get_article(article_id: str) -> dict:
    """Текст статьи + соседние ссылки и оглавление справа."""
    chapter_title, item = _find_article(article_id)
    if not item:
        # по-хорошему тут 404, но для заглушки вернём первую статью
        chapter_title, item = _find_article(_flat_ids()[0])

    # простая болванка текста
    paragraphs = [
        "Целями настоящего Федерального закона являются развитие рынков товаров, работ и услуг на основе соблюдения принципов добросовестной конкуренции...",
        "Закон обеспечивает единое экономическое пространство, реализацию прав потребителей на получение достоверной рекламы и т. д.",
        "Настоящая статья приведена как заглушка. Здесь будет реальный текст с разбивкой на пункты.",
    ]

    ids = _flat_ids()
    idx = ids.index(item["id"])
    prev_id = ids[idx - 1] if idx > 0 else None
    next_id = ids[idx + 1] if idx < len(ids) - 1 else None

    return {
        "title": LAW_TITLE,
        "meta": LAW_META,
        "article": {
            "id": item["id"],
            "heading": item["title"],
            "chapter": chapter_title,
            "paragraphs": paragraphs,
            "prev_id": prev_id,
            "next_id": next_id,
        },
        "toc": _TOC,
    }
