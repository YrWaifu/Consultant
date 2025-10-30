import json
import re
from datetime import datetime
from typing import Dict, Any
from pathlib import Path
from ..repositories.article_repository import ArticleRepository
from ..db import SessionLocal


class ArticleFileLoader:
    """Класс для загрузки статей из файлов различных форматов"""
    
    def __init__(self):
        db = SessionLocal()
        self.repository = ArticleRepository(db)
    
    def load_from_json(self, file_path: str) -> Dict[str, Any]:
        """Загрузка статей из JSON файла"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        result = {
            "categories_created": 0,
            "articles_created": 0,
            "errors": []
        }
        
        try:
            # Создаем категории
            if 'categories' in data:
                for cat_data in data['categories']:
                    try:
                        category = self.repository.create_category(**cat_data)
                        result["categories_created"] += 1
                    except Exception as e:
                        result["errors"].append(f"Ошибка создания категории {cat_data.get('name', 'Unknown')}: {str(e)}")
            
            # Создаем статьи
            if 'articles' in data:
                for article_data in data['articles']:
                    try:
                        # Находим категорию по слагу
                        category = self.repository.get_category_by_slug(article_data['category_slug'])
                        if not category:
                            result["errors"].append(f"Категория {article_data['category_slug']} не найдена")
                            continue
                        
                        # Создаем статью
                        article_data['category_id'] = category.id
                        del article_data['category_slug']  # Удаляем slug, так как передаем ID
                        
                        article = self.repository.create_article(**article_data)
                        result["articles_created"] += 1
                    except Exception as e:
                        result["errors"].append(f"Ошибка создания статьи {article_data.get('title', 'Unknown')}: {str(e)}")
        
        except Exception as e:
            result["errors"].append(f"Общая ошибка загрузки файла: {str(e)}")
        
        return result
    
    def load_from_markdown_directory(self, directory_path: str) -> Dict[str, Any]:
        """Загрузка статей из директории с Markdown файлами"""
        directory = Path(directory_path)
        if not directory.exists():
            return {"error": f"Директория {directory_path} не существует"}
        
        result = {
            "categories_created": 0,
            "articles_created": 0,
            "errors": []
        }
        
        # Создаем категории по умолчанию
        default_categories = [
            {
                "name": "Нужно знать при проверке рекламы",
                "slug": "ad-check-knowledge",
                "description": "Основные принципы и методики проверки рекламы",
                "icon": "📌",
                "sort_order": 1
            },
            {
                "name": "Обзоры от юристов",
                "slug": "lawyer-reviews", 
                "description": "Экспертные мнения и разъяснения",
                "icon": "📄",
                "sort_order": 2
            },
            {
                "name": "Интересные кейсы",
                "slug": "interesting-cases",
                "description": "Анализ реальных случаев нарушений",
                "icon": "💡",
                "sort_order": 3
            }
        ]
        
        # Создаем категории
        category_map = {}
        for cat_data in default_categories:
            try:
                category = self.repository.create_category(**cat_data)
                category_map[cat_data['slug']] = category
                result["categories_created"] += 1
            except Exception as e:
                result["errors"].append(f"Ошибка создания категории {cat_data['name']}: {str(e)}")

        # Обрабатываем Markdown файлы
        for md_file in directory.glob("*.md"):
            try:
                article_data = self._parse_markdown_file(md_file)
                if not article_data:
                    continue
                
                # Определяем категорию по имени файла или содержимому
                category_slug = article_data.get('category', 'ad-check-knowledge')
                if category_slug not in category_map:
                    category_slug = 'ad-check-knowledge'  # Fallback
                category = category_map[category_slug]
                # Создаем статью
                article_data['category_id'] = category.id
                del article_data['category']  # Удаляем поле category
                article = self.repository.create_article(**article_data)

                result["articles_created"] += 1
                
            except Exception as e:
                print(str(e))
                result["errors"].append(f"Ошибка обработки файла {md_file.name}: {str(e)}")
        
        return result
    
    def _parse_markdown_file(self, file_path: Path) -> Dict[str, Any]:
        """Парсинг Markdown файла для извлечения метаданных и контента"""
        content = file_path.read_text(encoding='utf-8')
        
        # Извлекаем frontmatter (YAML в начале файла)
        frontmatter = {}
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    import yaml
                    frontmatter = yaml.safe_load(parts[1]) or {}
                    content = parts[2].strip()
                except ImportError:
                    # Если YAML не установлен, парсим простой формат
                    frontmatter = self._parse_simple_frontmatter(parts[1])
                    content = parts[2].strip()
                except Exception:
                    # Если ошибка парсинга YAML, используем простой формат
                    frontmatter = self._parse_simple_frontmatter(parts[1])
                    content = parts[2].strip()
        
        # Извлекаем заголовок из первого заголовка Markdown, если он не указан в шапке
        title_match = re.match(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else file_path.stem
        
        # Создаем slug из заголовка, если он не указан
        slug = self._create_slug(title)
        
        # Извлекаем краткое описание (первый абзац), если оно не указано в шапке
        excerpt = None
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            para = para.strip()
            if para and not para.startswith('#'):
                excerpt = para[:200] + '...' if len(para) > 200 else para
                break
        
        return {
            'title': frontmatter.get('title', title),
            'slug': frontmatter.get('slug', slug),
            'excerpt': frontmatter.get('excerpt', excerpt),
            'content': content,
            'category': frontmatter.get('category', 'ad-check-knowledge'),
            'sort_order': frontmatter.get('sort_order', 0),
            'created_at': self._parse_date(frontmatter.get('created_at', None)),
        }
    
    def _parse_simple_frontmatter(self, frontmatter_text: str) -> Dict[str, Any]:
        """Простой парсинг frontmatter без YAML"""
        result = {}
        for line in frontmatter_text.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                result[key.strip()] = value.strip().strip('"\'')
        return result
    
    def _create_slug(self, title: str) -> str:
        """Создание URL-слага из заголовка"""
        # Транслитерация кириллицы
        translit_map = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
            'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
            'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
            'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
            'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
        }
        
        slug = title.lower()
        for cyr, lat in translit_map.items():
            slug = slug.replace(cyr, lat)
        
        # Заменяем пробелы и специальные символы на дефисы
        slug = re.sub(r'[^\w\-]', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        
        return slug
    
    def _parse_date(self, date_str: str) -> datetime:
        """Парсинг даты из строки"""
        if not date_str:
            return datetime.utcnow()
        
        try:
            # Пробуем разные форматы
            formats = ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
        except:
            pass
        
        return datetime.utcnow()
    
    def create_sample_data(self) -> Dict[str, Any]:
        """Создание примеров данных для демонстрации"""
        from .article_service import ArticleService
        article_service = ArticleService()
        return article_service.create_sample_data()
