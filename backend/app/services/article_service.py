from datetime import datetime
from typing import List, Optional
from ..repositories.article_repository import ArticleRepository
from ..models import Article, ArticleCategory
from ..db import SessionLocal


class ArticleService:
    def __init__(self):
        db = SessionLocal()
        self.repository = ArticleRepository(db)

    def get_articles_homepage(self) -> dict:
        """Получить данные для главной страницы статей с тремя блоками"""
        categories = self.repository.get_categories()
        
        # Получаем статьи для каждой категории (по 4 для первой, по 3 для остальных)
        blocks = []
        for i, category in enumerate(categories[:3]):  # Только первые 3 категории
            limit = 4 if i == 0 else 3  # Первый блок - 4 статьи, остальные - по 3
            articles = self.repository.get_articles_by_category(category.slug, limit=limit)
            
            blocks.append({
                "category": category,
                "articles": articles
            })
        
        return {
            "blocks": blocks,
            "total_categories": len(categories)
        }

    def get_category_articles(self, category_slug: str) -> Optional[dict]:
        """Получить все статьи категории"""
        category = self.repository.get_category_by_slug(category_slug)
        if not category:
            return None
        
        articles = self.repository.get_articles_by_category(category_slug)
        
        return {
            "category": category,
            "articles": articles
        }

    def get_article_detail(self, slug: str) -> Optional[dict]:
        """Получить детальную информацию о статье"""
        article = self.repository.get_article_by_slug(slug)
        if not article:
            return None
        
        # Увеличиваем счетчик просмотров
        self.repository.increment_view_count(article.id)
        
        # Получаем связанные статьи из той же категории
        related_articles = self.repository.get_articles_by_category(
            article.category.slug, limit=5
        )
        # Исключаем текущую статью
        related_articles = [a for a in related_articles if a.id != article.id]
        
        return {
            "article": article,
            "related_articles": related_articles[:4]  # Максимум 4 связанные статьи
        }

    def search_articles(self, query: str) -> List[Article]:
        """Поиск статей"""
        return self.repository.search_articles(query)

    def get_latest_articles(self, limit: int = 10) -> List[Article]:
        """Получить последние статьи"""
        return self.repository.get_latest_articles(limit)

    def create_sample_data(self):
        """Создать примеры данных для демонстрации"""
        # Создаем категории
        categories_data = [
            {
                "name": "Нужно знать при проверке рекламы",
                "slug": "ad-check-knowledge",
                "description": "Основные принципы и методики проверки рекламы на соответствие требованиям закона",
                "icon": "📌",
                "sort_order": 1
            },
            {
                "name": "Обзоры от юристов",
                "slug": "lawyer-reviews",
                "description": "Экспертные мнения и разъяснения от практикующих юристов",
                "icon": "📄",
                "sort_order": 2
            },
            {
                "name": "Интересные кейсы",
                "slug": "interesting-cases",
                "description": "Анализ реальных случаев нарушений и спорных ситуаций в рекламе",
                "icon": "💡",
                "sort_order": 3
            }
        ]

        # Создаем категории (проверяем на существование)
        created_categories = []
        for cat_data in categories_data:
            # Проверяем, существует ли категория
            existing_category = self.repository.get_category_by_slug(cat_data["slug"])
            if existing_category:
                created_categories.append(existing_category)
            else:
                try:
                    category = self.repository.create_category(**cat_data)
                    created_categories.append(category)
                except Exception as e:
                    print(f"⚠️  Ошибка создания категории {cat_data['name']}: {e}")
                    # Пытаемся найти существующую категорию
                    existing = self.repository.get_category_by_slug(cat_data["slug"])
                    if existing:
                        created_categories.append(existing)

        # Создаем статьи для первой категории
        articles_data = [
            {
                "title": "Методика оценивания",
                "slug": "assessment-methodology",
                "excerpt": "Как проводится проверка рекламы: критерии, этапы и принципы оценки",
                "content": "Проверка рекламы на соответствие требованиям Федерального закона «О рекламе» включает несколько этапов. Сначала анализируется текст рекламы на предмет использования запрещенных формулировок, затем проверяется соответствие требованиям к конкретным видам товаров и услуг. Особое внимание уделяется проверке достоверности информации и отсутствию вводящих в заблуждение утверждений.",
                "author": "Эксперт по рекламному праву",
                "sort_order": 1
            },
            {
                "title": "Перечень нарушений",
                "slug": "violations-list",
                "excerpt": "Обзор основных нарушений рекламного законодательства с примерами и разъяснениями юристов",
                "content": "К наиболее распространенным нарушениям рекламного законодательства относятся: использование превосходных степеней сравнения без документального подтверждения, недостоверная информация о товаре, скрытая реклама, нарушение требований к рекламе отдельных видов товаров. Каждое нарушение влечет за собой административную ответственность в виде штрафов.",
                "author": "Юрист-практик",
                "sort_order": 2
            },
            {
                "title": "Виды ответственности в сфере рекламы",
                "slug": "advertising-liability-types",
                "excerpt": "Санкции за нарушения рекламного законодательства: административные штрафы, предупреждения и другие меры",
                "content": "За нарушения рекламного законодательства предусмотрена административная ответственность. Размер штрафов зависит от характера нарушения и субъекта правонарушения. Для физических лиц штрафы составляют от 2 до 2,5 тысяч рублей, для должностных лиц - от 4 до 20 тысяч рублей, для юридических лиц - от 100 тысяч до 500 тысяч рублей.",
                "author": "Специалист по административному праву",
                "sort_order": 3
            },
            {
                "title": "Недостоверность - это?",
                "slug": "what-is-unreliability",
                "excerpt": "Что считается недостоверной информацией в рекламе, как избежать нарушений и правильно формулировать утверждения",
                "content": "Недостоверной считается информация, не соответствующая действительности. В рекламе это может выражаться в завышении характеристик товара, искажении фактов о его свойствах или результатах использования. Чтобы избежать нарушений, необходимо основывать все утверждения на документально подтвержденных данных и избегать формулировок, которые могут ввести потребителя в заблуждение.",
                "author": "Эксперт по потребительскому праву",
                "sort_order": 4
            }
        ]

        # Создаем статьи для второй категории
        lawyer_articles = [
            {
                "title": "Правовые границы рекламы",
                "slug": "legal-advertising-boundaries",
                "excerpt": "Где проходит грань между рекламой, информированием и новостями, и что закон считает рекламой",
                "content": "Определение рекламы в законе достаточно широкое и включает любую информацию, направленную на привлечение внимания к товару или услуге. Важно различать рекламу от информирования потребителей и новостной информации. Критерием является цель сообщения - если оно направлено на продвижение товара или услуги, то это реклама.",
                "author": "Кандидат юридических наук",
                "sort_order": 1
            },
            {
                "title": "От товара до идеи",
                "slug": "from-product-to-idea",
                "excerpt": "Что может быть объектом рекламы согласно ФЗ «О рекламе»: товары, услуги, бренды и общественные инициативы",
                "content": "Объектом рекламы может быть не только конкретный товар или услуга, но и торговая марка, бренд, общественная инициатива или социальная кампания. Закон регулирует рекламу всех видов деятельности, направленной на получение прибыли или достижение иных целей. Важно учитывать специфику каждого типа рекламируемого объекта.",
                "author": "Практикующий юрист",
                "sort_order": 2
            },
            {
                "title": "Обязательное информирование и реклама",
                "slug": "mandatory-info-and-advertising",
                "excerpt": "Практические рекомендации для операторов связи и компаний по совмещению информирования абонентов с требованиями ФЗ «О рекламе»",
                "content": "Операторы связи и другие компании часто сталкиваются с необходимостью информировать клиентов о своих услугах. Важно разграничивать обязательное информирование от рекламы. Информация, которую компания обязана предоставить по закону, не является рекламой, но если она содержит элементы привлечения внимания к услугам, то может подпадать под действие рекламного законодательства.",
                "author": "Специалист по телекоммуникационному праву",
                "sort_order": 3
            }
        ]

        # Создаем статьи для третьей категории
        cases_articles = [
            {
                "title": "Гроб для подружки с дизайном Лабубу",
                "slug": "coffin-labubu-design",
                "excerpt": "Необычный пример продвижения ритуальных услуг в Instagram: где проходит грань между оригинальностью и этическими нормами",
                "content": "Ритуальное агентство в социальных сетях использовало популярный дизайн персонажа Лабубу для продвижения своих услуг. Это вызвало широкое обсуждение в обществе. С правовой точки зрения, такая реклама не нарушает закон «О рекламе», но может противоречить этическим нормам и общественной морали. Важно учитывать культурные особенности и чувства людей при создании рекламы.",
                "author": "Эксперт по этике в рекламе",
                "sort_order": 1
            },
            {
                "title": "Кофе с намёком",
                "slug": "coffee-with-hint",
                "excerpt": "Скандальный дизайн кофейни с женскими лицами и стаканами в форме позвоночника: творческие границы и визуальные решения в рекламе",
                "content": "Кофейня использовала провокационный дизайн с изображениями женских лиц и стаканов в форме позвоночника. Это вызвало общественный резонанс и жалобы в ФАС. Суд признал такую рекламу неэтичной и нарушающей общественные нормы. Дело показало важность учета культурных особенностей и этических норм при создании рекламных материалов.",
                "author": "Специалист по рекламной этике",
                "sort_order": 2
            },
            {
                "title": "«Вставь мне»",
                "slug": "insert-me",
                "excerpt": "Случай, когда реклама стоматологии в Тюмени была признана непристойной из-за двусмысленного слогана",
                "content": "Стоматологическая клиника использовала слоган «Вставь мне», который был признан непристойным и нарушающим общественные нормы. ФАС вынесла предупреждение, а суд поддержал позицию антимонопольной службы. Дело показало, что даже игра слов должна учитывать нормы приличия и не нарушать общественную мораль. Важно тестировать рекламные материалы на восприятие различными группами аудитории.",
                "author": "Юрист по рекламным спорам",
                "sort_order": 3
            }
        ]

        # Создаем все статьи
        all_articles = [
            (created_categories[0].id, articles_data),
            (created_categories[1].id, lawyer_articles),
            (created_categories[2].id, cases_articles)
        ]

        articles_created_count = 0
        for category_id, articles in all_articles:
            for article_data in articles:
                # Проверяем, существует ли статья
                if not self.repository.article_exists_by_slug(article_data["slug"]):
                    try:
                        self.repository.create_article(category_id=category_id, **article_data)
                        articles_created_count += 1
                    except Exception as e:
                        print(f"⚠️  Ошибка создания статьи {article_data['title']}: {e}")

        return {
            "categories_created": len(created_categories),
            "articles_created": articles_created_count
        }
