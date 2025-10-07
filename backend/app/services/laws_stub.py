from __future__ import annotations
from ..db import SessionLocal
from ..repositories.law_repository import LawRepository

LAW_TITLE = 'Федеральный закон «О рекламе»'
LAW_META = 'от 13.03.2006 N 38-ФЗ'
LAW_CODE = "38-FZ"

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
    """Список разделов/статей закона из БД с правильной группировкой."""
    db = SessionLocal()
    repo = LawRepository(db)
    
    try:
        # Получаем активную версию закона
        law_version = repo.get_active_version(LAW_CODE)
        
        if not law_version:
            # Если в БД пусто, возвращаем старую заглушку
            return {"title": LAW_TITLE, "meta": LAW_META, "toc": _TOC}
        
        # Получаем главы
        chapters = repo.get_chapters_by_version(law_version.id)
        
        # Формируем структуру TOC: каждая глава со своими статьями
        toc = []
        
        for chapter in chapters:
            # Получаем статьи этой главы
            articles = repo.get_articles_by_chapter(chapter.id)
            
            # Сортируем статьи по номеру (числовая сортировка)
            def article_sort_key(art):
                try:
                    return float(art.article_number)
                except:
                    return 99999
            
            articles.sort(key=article_sort_key)
            
            chapter_toc = {
                "chapter": chapter.title,
                "items": []
            }
            
            for article in articles:
                chapter_toc["items"].append({
                    "id": f"art-{article.article_number}",
                    "title": article.title,
                })
            
            toc.append(chapter_toc)
        
        return {
            "title": law_version.law_name,
            "meta": "",  
            "toc": toc if toc else _TOC
        }
        
    finally:
        db.close()


def _flat_ids():
    return [it["id"] for ch in _TOC for it in ch["items"]]


def _find_article(article_id: str):
    for ch in _TOC:
        for it in ch["items"]:
            if it["id"] == article_id:
                return ch["chapter"], it
    return None, None


def get_article(article_id: str) -> dict:
    """Текст статьи + соседние ссылки и оглавление справа (из БД)."""
    db = SessionLocal()
    repo = LawRepository(db)
    
    try:
        # Получаем активную версию
        law_version = repo.get_active_version(LAW_CODE)
        
        if not law_version:
            # Fallback на заглушку
            chapter_title, item = _find_article(article_id)
            if not item:
                chapter_title, item = _find_article(_flat_ids()[0])
            
            paragraphs = [
                "Целями настоящего Федерального закона являются развитие рынков товаров...",
            ]
            
            return {
                "title": LAW_TITLE,
                "meta": LAW_META,
                "article": {
                    "id": item["id"],
                    "heading": item["title"],
                    "chapter": chapter_title,
                    "paragraphs": paragraphs,
                    "prev_id": None,
                    "next_id": None,
                },
                "toc": _TOC,
            }
        
        # Извлекаем номер статьи из article_id (например: "art-5" → "5")
        article_number = article_id.replace("art-", "")
        
        # Ищем статью в БД через репозиторий
        article = repo.get_article_by_number(law_version.id, article_number)
        
        if not article:
            # Берем первую статью
            article = repo.get_first_article(law_version.id)
        
        # Используем HTML если есть, иначе plain text
        if article.content_html:
            paragraphs = [article.content_html]
        else:
            paragraphs = [p.strip() for p in article.content.split("\n\n") if p.strip()]
        
        # Получаем соседние статьи
        all_articles = repo.get_articles_by_version(law_version.id)
        
        # Сортируем статьи по номеру (числовая сортировка)
        def article_sort_key(art):
            try:
                return float(art.article_number)
            except:
                return 99999
        
        all_articles.sort(key=article_sort_key)
        
        article_ids = [f"art-{a.article_number}" for a in all_articles]
        current_id = f"art-{article.article_number}"
        
        try:
            idx = article_ids.index(current_id)
            prev_id = article_ids[idx - 1] if idx > 0 else None
            next_id = article_ids[idx + 1] if idx < len(article_ids) - 1 else None
        except ValueError:
            prev_id = next_id = None
        
        # Получаем TOC
        toc_data = get_law_index()
        
        return {
            "title": law_version.law_name,
            "meta": "",
            "article": {
                "id": current_id,
                "heading": article.title,
                "chapter": "",
                "paragraphs": paragraphs,
                "prev_id": prev_id,
                "next_id": next_id,
                "source_url": article.source_url,
            },
            "toc": toc_data.get("toc", []),
        }
        
    finally:
        db.close()


def search_laws(q: str | None = None) -> list[dict]:
    """Поиск по статьям закона (из БД с full-text search)."""
    if not q:
        return []
    
    db = SessionLocal()
    repo = LawRepository(db)
    
    try:
        # Получаем активную версию
        law_version = repo.get_active_version(LAW_CODE)
        
        if not law_version:
            # Fallback на заглушку
            ql = q.strip().lower()
            results = []
            for ch in _TOC:
                for item in ch["items"]:
                    if ql in item["title"].lower() or ql in ch["chapter"].lower():
                        results.append({
                            "id": item["id"],
                            "title": item["title"],
                            "chapter": ch["chapter"],
                        })
            return results
        
        # Поиск в БД через репозиторий
        articles = repo.search_articles(law_version.id, q, limit=20)
        
        results = []
        for article in articles:
            results.append({
                "id": f"art-{article.article_number}",
                "title": article.title,
                "chapter": "",
            })
        
        return results
        
    finally:
        db.close()