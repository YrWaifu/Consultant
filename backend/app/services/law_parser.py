"""
Парсер закона «О рекламе» с КонсультантПлюс.
Адаптировано из drafts/parse.py для сохранения в PostgreSQL.
"""
import re
import time
import urllib.parse
from typing import List, Tuple, Dict
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup, Tag
from sqlalchemy.orm import Session

from ..db import SessionLocal, engine
from ..repositories.law_repository import LawRepository


# Константы
LAW_BASE_URL = "https://www.consultant.ru/document/cons_doc_LAW_58968/"
LAW_NAME_URL = "https://www.consultant.ru/cons/cgi/online.cgi?req=doc&base=LAW&n=502629&dst=1000000001&cacheid=4FB90E0190495F8EA6306FE02560E6E3&mode=splus&rnd=Fkqfx1VCH2OzPk481#misfx1V6LzxmMZJm2"
LAW_NAME = "Федеральный закон от 13.03.2006 N 38-ФЗ \"О рекламе\""
LAW_CODE = "38-FZ"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; law-scraper/1.0; +https://example.invalid)",
    "Accept-Language": "ru-RU,ru;q=0.9"
})


# -------------------- NETWORK -------------------- #
def fetch(url: str, *, retries: int = 3, sleep: float = 1.0) -> str:
    """Загрузка страницы с повторными попытками"""
    last_exc = None
    for i in range(retries):
        try:
            resp = SESSION.get(url, timeout=20)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            last_exc = e
            time.sleep(sleep * (i + 1))
    raise last_exc


# -------------------- HELPERS -------------------- #
def absolute(href: str, base: str) -> str:
    """Преобразование относительной ссылки в абсолютную"""
    return urllib.parse.urljoin(base, href)


# -------------------- TOC PARSING -------------------- #
def extract_structured_links(html: str, toc_url: str) -> List[Dict]:
    """
    Извлечение структурированных ссылок: главы и их статьи.
    Возвращает список словарей: {"type": "chapter", "title": "...", "url": "...", "articles": [...]}
    """
    soup = BeautifulSoup(html, "lxml")
    allowed_prefix = "/document/cons_doc_LAW_58968/"
    structure = []
    
    # Ищем все ссылки подряд, формируем структуру
    all_links = soup.find_all("a", href=True)
    current_chapter = None
    seen_urls = set()  # Защита от дубликатов
    
    for link in all_links:
        href = link["href"].strip()
        if not href.startswith(allowed_prefix):
            continue
        
        title = " ".join(link.get_text(" ", strip=True).split())
        if not title:
            continue
            
        url = absolute(href, toc_url)
        if "#" in url:
            url = url.split("#", 1)[0]
        
        # Пропускаем корневой URL и дубликаты
        if url.rstrip("/") == toc_url.rstrip("/") or url in seen_urls:
            continue
        
        seen_urls.add(url)
        
        # Это глава?
        if title.startswith("Глава"):
            current_chapter = {
                "type": "chapter",
                "title": title,
                "url": url,
                "articles": []
            }
            structure.append(current_chapter)
        
        # Это статья?
        elif title.startswith("Статья") and current_chapter:
            current_chapter["articles"].append({
                "title": title,
                "url": url
            })
    
    return structure


# -------------------- CONTENT PARSING -------------------- #
def clean_node_text(node: Tag) -> str:
    """Извлечение и очистка текста из HTML с сохранением структуры"""
    # Удаление мусора
    for sel in [
        ".info-link", ".document__insert", ".document__edit",
        ".dnk-button-dummy", ".document-page__balloon",
        ".full-text", ".document-page__banner-middle",
    ]:
        for bad in node.select(sel):
            bad.decompose()
    
    for bad in node.find_all(["script", "style", "noscript"]):
        bad.decompose()

    # Собираем текст с сохранением структуры
    text = node.get_text("\n", strip=True)
    
    # Разбиваем на строки и форматируем
    lines = []
    
    i = 0
    text_lines = [l.strip() for l in text.split("\n") if l.strip()]
    
    while i < len(text_lines):
        line = text_lines[i]
        
        # Основные пункты (1., 2., 3., 3.1. и т.д.)
        if re.match(r'^\d+(\.\d+)?\.', line):
            # Склеиваем с последующими строками до следующего пункта
            full_line = line
            i += 1
            while i < len(text_lines) and not re.match(r'^(\d+(\.\d+)?\.|[а-я]\)|\d+\))', text_lines[i]):
                full_line += " " + text_lines[i]
                i += 1
            lines.append(f"\n\n{full_line}")
            continue
        
        # Подпункты с номерами (1), 2), 3)) - для определений
        elif re.match(r'^\d+\)$', line):  # Только номер без текста
            # Склеиваем следующую строку (определение)
            i += 1
            if i < len(text_lines):
                definition = text_lines[i]
                # Продолжаем склеивать до следующего номера
                i += 1
                while i < len(text_lines) and not re.match(r'^(\d+\)|[а-я]\)|\d+(\.\d+)?\.)', text_lines[i]):
                    definition += " " + text_lines[i]
                    i += 1
                lines.append(f"\n{line} {definition}")
            else:
                lines.append(f"\n{line}")
            continue
        
        # Подпункты с буквами (а), б), в))
        elif re.match(r'^[а-я]\)$', line, re.IGNORECASE):
            i += 1
            if i < len(text_lines):
                definition = text_lines[i]
                i += 1
                while i < len(text_lines) and not re.match(r'^([а-я]\)|\d+\)|\d+(\.\d+)?\.)', text_lines[i]):
                    definition += " " + text_lines[i]
                    i += 1
                lines.append(f"\n  {line} {definition}")
            else:
                lines.append(f"\n  {line}")
            continue
        
        # Обычная строка
        if lines:
            lines[-1] += " " + line
        else:
            lines.append(line)
        i += 1
    
    text = "\n".join(lines)
    
    # Очистка
    text = re.sub(r" +", " ", text)  # Убираем множественные пробелы
    text = re.sub(r"\n{4,}", "\n\n", text)  # Максимум 2 переноса подряд
    
    return text.strip()


def extract_clean_html(node: Tag) -> str:
    """Извлечение очищенного HTML с сохранением форматирования"""
    # Удаление мусора и заголовков
    for sel in [
        ".info-link", ".document__insert", ".document__edit",
        ".dnk-button-dummy", ".document-page__balloon",
        ".full-text", ".document-page__banner-middle",
        "h1", "h2", "h3"  # Убираем заголовки (они отдельно)
    ]:
        for bad in node.select(sel):
            bad.decompose()
    
    for bad in node.find_all(["script", "style", "noscript"]):
        bad.decompose()
    
    # Ищем ВСЕ параграфы с текстом "Статья N..." и удаляем (дубликаты заголовков)
    for p in node.find_all("p"):
        text = p.get_text(strip=True)
        # Если параграф содержит только заголовок статьи - удаляем
        if re.match(r'^Статья\s+\d+[\.\d]*\.\s+.+$', text) and len(text) < 200:
            p.decompose()
    
    # Получаем HTML
    html = str(node)
    
    # Очистка лишних классов и атрибутов
    html = re.sub(r'class="[^"]*"', '', html)
    html = re.sub(r'style="[^"]*"', '', html)
    html = re.sub(r'id="[^"]*"', '', html)
    html = re.sub(r'data-[a-z-]+="[^"]*"', '', html)
    
    # Убираем пустые теги
    html = re.sub(r'<p>\s*</p>', '', html)
    html = re.sub(r'<div>\s*</div>', '', html)
    
    return html.strip()


def parse_article_page(html: str, url: str) -> Dict[str, str]:
    """Парсинг страницы статьи/главы"""
    soup = BeautifulSoup(html, "lxml")
    
    # Извлечение заголовка
    title = ""
    title_el = soup.select_one(".document-page__content .doc-style h1")
    if title_el:
        title = " ".join(title_el.get_text(" ", strip=True).split())
    if not title:
        bc = soup.select_one(".document-page__breadcrumbs li:last-child")
        if bc:
            title = bc.get_text(" ", strip=True)
    if not title:
        title = soup.title.get_text(" ", strip=True) if soup.title else url

    # Извлечение контента
    content_root = soup.select_one(".document-page__content")
    if not content_root:
        content_root = soup.select_one("section.document-page__main") or soup

    # Plain text для поиска
    body_text = clean_node_text(content_root)
    
    # HTML для отображения
    body_html = extract_clean_html(content_root)
    
    return {"title": title, "content": body_text, "content_html": body_html, "url": url}


# -------------------- DATABASE OPERATIONS -------------------- #
def save_to_database(structure: List[Dict], version_date: date, law_name: str = LAW_NAME) -> None:
    """Сохранение спарсенных данных в БД со связями глава-статьи"""
    db = SessionLocal()
    repo = LawRepository(db)
    
    try:
        # 1. Деактивировать старые версии
        repo.deactivate_versions(LAW_CODE)
        
        # 2. Создать новую версию
        law_version = repo.create_version(
            law_name=law_name,
            law_code=LAW_CODE,
            source_url=LAW_BASE_URL,
            version_date=version_date,
            is_active=True
        )
        
        print(f"✅ Создана версия закона ID={law_version.id}, дата={version_date}")
        
        # 3. Парсинг и сохранение по структуре: глава → статьи
        total_count = 0
        for chapter_data in structure:
            # Парсим главу
            print(f"[Глава] Парсю: {chapter_data['title']}")
            
            try:
                html = fetch(chapter_data["url"])
                parsed = parse_article_page(html, chapter_data["url"])
                
                match = re.search(r"Глава\s+(\d+)", chapter_data["title"])
                chapter_num = int(match.group(1)) if match else 0
                
                chapter = repo.create_chapter(
                    version_id=law_version.id,
                    chapter_number=chapter_num,
                    title=parsed["title"],
                    content=parsed["content"],
                    source_url=parsed["url"]
                )
                total_count += 1
                
            except Exception as e:
                print(f"  ⚠️ Ошибка парсинга главы: {e}")
                continue
            
            # Парсим статьи этой главы
            for article_data in chapter_data["articles"]:
                print(f"  [Статья] Парсю: {article_data['title']}")
                
                try:
                    html = fetch(article_data["url"])
                    parsed = parse_article_page(html, article_data["url"])
                    
                    match = re.search(r"Статья\s+(\d+(?:\.\d+)?)", article_data["title"])
                    article_num = match.group(1) if match else "0"
                    
                    repo.create_article(
                        version_id=law_version.id,
                        chapter_id=chapter.id,
                        article_number=article_num,
                        title=parsed["title"],
                        content=parsed["content"],
                        content_html=parsed.get("content_html"),
                        source_url=parsed["url"]
                    )
                    total_count += 1
                    
                    # Коммитим каждые 5 записей
                    if total_count % 5 == 0:
                        repo.bulk_commit()
                    
                    time.sleep(0.7)  # Задержка между запросами
                    
                except Exception as e:
                    print(f"    ⚠️ Ошибка парсинга статьи: {e}")
                    continue
        
        repo.bulk_commit()
        print(f"✅ Сохранено {total_count} документов в БД")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка сохранения в БД: {e}")
        raise
    finally:
        db.close()


def fetch_law_name() -> str:
    """Получение названия закона с указанного URL"""
    try:
        # Пробуем получить HTML версию с дополнительными заголовками
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        resp = SESSION.get(LAW_NAME_URL, headers=headers, timeout=20)
        resp.raise_for_status()
        html = resp.text
        
        # Парсим как HTML (даже если это XML, BeautifulSoup может обработать)
        soup = BeautifulSoup(html, "lxml")
        
        # Ищем название в теге <title> или в <meta property="og:title">
        full_name = None
        
        # Пробуем найти в <meta property="og:title">
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            full_name = og_title.get("content")
        
        # Если не нашли, пробуем в <title>
        if not full_name:
            title_el = soup.find("title")
            if title_el:
                full_name = title_el.get_text(strip=True)
        
        if full_name:
            # Убираем " - КонсультантПлюс" в конце, если есть
            full_name = re.sub(r'\s*-\s*КонсультантПлюс\s*$', '', full_name, flags=re.IGNORECASE)
            
            # Убираем ТОЛЬКО последнюю скобку "(с изм. и доп., вступ. в силу с...)"
            # Оставляем все остальное, включая "(ред. от...)" 
            result = re.sub(r'\s*\(с\s+изм\.\s+и\s+доп\..*?\)$', '', full_name)
            result = result.strip()
            
            print(f"✅ Название закона получено: {result}")
            return result
        
        print(f"⚠️ Название закона не найдено в <title> или <meta property=\"og:title\">")
        print(f"⚠️ Использую fallback название: {LAW_NAME}")
        return LAW_NAME  # fallback
    except Exception as e:
        print(f"❌ Ошибка при получении названия закона с {LAW_NAME_URL}: {e}")
        import traceback
        traceback.print_exc()
        print(f"⚠️ Использую fallback название: {LAW_NAME}")
        return LAW_NAME  # fallback


def extract_law_metadata(html: str) -> Dict:
    """Извлечение метаданных закона: название и дата из названия"""
    soup = BeautifulSoup(html, "lxml")
    
    # Получаем название закона с указанного URL
    law_name = fetch_law_name()
    law_date = date(2006, 3, 13)  # default
    
    # Извлекаем дату из названия: "Федеральный закон от 13.03.2006 N 38-ФЗ (ред. от 31.07.2025) "О рекламе""
    date_match = re.search(r'от\s+(\d{2}\.\d{2}\.\d{4})', law_name)
    if date_match:
        try:
            law_date = datetime.strptime(date_match.group(1), '%d.%m.%Y').date()
        except:
            pass
    
    return {
        "law_name": law_name,
        "version_date": law_date
    }


# -------------------- MAIN FUNCTION -------------------- #
def parse_and_save_law(law_url: str = LAW_BASE_URL) -> None:
    """
    Основная функция парсинга закона и сохранения в БД.
    Вызывается вручную через manage.py или автоматически через RQ.
    """
    print(f"🔍 Начинаю парсинг закона: {law_url}")
    
    # 1. Загрузка оглавления
    toc_html = fetch(law_url)
    
    # 2. Извлечение метаданных
    metadata = extract_law_metadata(toc_html)
    print(f"📋 Закон: {metadata['law_name']}")
    print(f"📅 Дата последней редакции: {metadata['version_date']}")
    
    # 3. Извлечение структуры
    structure = extract_structured_links(toc_html, law_url)
    
    # Подсчет общего количества документов
    total_docs = len(structure) + sum(len(ch["articles"]) for ch in structure)
    print(f"📚 Найдено {len(structure)} глав, {total_docs} документов для парсинга")
    
    # 4. Сохранение в БД со структурой и метаданными
    save_to_database(structure, metadata["version_date"], metadata["law_name"])
    
    print("🎉 Парсинг закона завершён успешно!")

