# -*- coding: utf-8 -*-
# parse.py — универсальный парсер КонсультантПлюс для выгрузки закона в Markdown
#
# requirements:
#   pip install requests beautifulsoup4 lxml
#
# usage:
#   python parse.py --root https://www.consultant.ru/document/cons_doc_LAW_58968/ --out ./out --md

import argparse
import pathlib
import re
import time
import sys
import urllib.parse
from typing import List, Tuple, Dict

import requests
from bs4 import BeautifulSoup, Tag

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; law-scraper/1.0; +https://example.invalid)",
    "Accept-Language": "ru-RU,ru;q=0.9"
})


# -------------------- CLI -------------------- #
def parse_args():
    p = argparse.ArgumentParser(description="Парсер КонсультантПлюс → Markdown")
    p.add_argument("--root",
                   default="https://www.consultant.ru/document/cons_doc_LAW_58968/",
                   help="URL страницы оглавления закона")
    p.add_argument("--out",
                   default="out/LAW_58968",
                   help="Папка для сохранения .md файлов")
    p.add_argument("--md",
                   action="store_true",
                   help="Флаг совместимости, ни на что не влияет (всё и так в .md)")
    return p.parse_args()


# -------------------- NETWORK -------------------- #
def fetch(url: str, *, retries: int = 3, sleep: float = 1.0) -> str:
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
    return urllib.parse.urljoin(base, href)


def sanitize_filename(name: str) -> str:
    name = re.sub(r"[\\/:*?\"<>|]", "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:180]


# -------------------- TOC PARSING -------------------- #
def extract_links_from_toc(html: str, toc_url: str) -> List[Tuple[str, str]]:
    soup = BeautifulSoup(html, "lxml")
    allowed_prefix = "/document/cons_doc_LAW_58968/"
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(allowed_prefix):
            title = " ".join(a.get_text(" ", strip=True).split())
            url = absolute(href, toc_url)
            if "#" in url:
                url = url.split("#", 1)[0]
            if url.rstrip("/") == toc_url.rstrip("/"):
                continue
            links.append((title, url))
    # уникальные
    seen = set()
    uniq = []
    for t, u in links:
        if u not in seen:
            seen.add(u)
            uniq.append((t, u))
    return uniq


# -------------------- CONTENT PARSING -------------------- #
def clean_node_text(node: Tag) -> str:
    # вычищаем мусор
    for sel in [
        ".info-link", ".document__insert", ".document__edit",
        ".dnk-button-dummy", ".document-page__balloon",
        ".full-text", ".document-page__banner-middle",
    ]:
        for bad in node.select(sel):
            bad.decompose()
    for bad in node.find_all(["script", "style", "noscript"]):
        bad.decompose()

    text_parts = []
    for el in node.descendants:
        if isinstance(el, Tag):
            if el.name in ["h1", "h2", "h3", "h4"]:
                text_parts.append("\n\n# " + el.get_text(" ", strip=True) + "\n\n")
            if el.name in ["p", "li"]:
                text_parts.append(el.get_text(" ", strip=True) + "\n")
            if el.name == "br":
                text_parts.append("\n")

    text = "".join(text_parts)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_article_page(html: str, url: str) -> Dict[str, str]:
    soup = BeautifulSoup(html, "lxml")
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

    content_root = soup.select_one(".document-page__content")
    if not content_root:
        content_root = soup.select_one("section.document-page__main") or soup

    body_md = clean_node_text(content_root)
    title_line = f"# {title}".strip()
    meta = f"\n\n> Источник: {url}\n"
    return {"title": title, "markdown": f"{title_line}\n{meta}\n{body_md}\n"}


# -------------------- MAIN -------------------- #
def main():
    args = parse_args()
    base_toc_url = args.root.strip()
    if not re.match(r"^https?://", base_toc_url, re.I):
        raise SystemExit(f"[x] Неверный URL для --root: {base_toc_url}")

    out_dir = pathlib.Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[i] Читаю оглавление: {base_toc_url}")
    toc_html = fetch(base_toc_url)
    links = extract_links_from_toc(toc_html, base_toc_url)
    links = [(t, u) for t, u in links if "/document/cons_doc_LAW_58968/" in u]

    def sort_key(x):
        t = x[0]
        m = re.search(r"(Статья|Глава)\s+(\d+(?:\.\d+)?)", t)
        if m:
            kind = 0 if m.group(1) == "Глава" else 1
            try:
                num = float(m.group(2))
            except:
                num = 99999
            return (kind, num, t)
        return (2, 99999, t)

    links.sort(key=sort_key)

    index_lines = [
        "# Федеральный закон «О рекламе» — выгрузка в Markdown\n",
        f"> Сгенерировано из {base_toc_url}\n"
    ]

    for idx, (title, url) in enumerate(links, 1):
        print(f"[{idx}/{len(links)}] Парсю: {title} | {url}")
        try:
            html = fetch(url)
        except Exception as e:
            print(f"  [!] Пропускаю: {e}")
            continue

        parsed = parse_article_page(html, url)

        if title.startswith("Глава"):
            m = re.search(r"Глава\s+(\d+)", title)
            num = int(m.group(1)) if m else idx
            fname_prefix = f"{num:02d}_Глава"
        elif title.startswith("Статья"):
            m = re.search(r"Статья\s+(\d+(?:\.\d+)?)", title)
            num = m.group(1) if m else str(idx)
            num_for_file = num.replace(".", "_")
            fname_prefix = f"{float(num):06.2f}_Статья" if num.replace(".", "", 1).isdigit() else f"{num_for_file}_Статья"
        else:
            fname_prefix = f"{idx:04d}_Прочее"

        fname = f"{fname_prefix}__{sanitize_filename(title)}.md"
        fpath = out_dir / fname
        fpath.write_text(parsed["markdown"], encoding="utf-8")

        index_lines.append(f"- [{title}]({fname})")
        time.sleep(0.7)

    (out_dir / "INDEX.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"\n[i] Готово. Файлы в: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
