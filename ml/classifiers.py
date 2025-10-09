import os
import json
import re
from huggingface_hub import InferenceClient
from collections import defaultdict

from ml.dictionaries import *

"""
Модуль поиска нарушений в текстовой рекламе
"""

client = InferenceClient(
    model=os.environ["MODEL"],
    token=os.environ["HF_TOKEN"]
)


def form_prompt(ad_text: str) -> str:
    """
    Формирует промпт
    :param ad_text: текст рекламы
    :return: str - текст запроса к LLM
    """

    return f"""
            Ты — эксперт по законодательству о рекламе РФ.
            Анализируй текст рекламы и ответь на каждый вопрос "ДА" или "НЕТ". Если ответ "ДА", добавь рекомендацию по исправлению этого нарушения.
            Формат ответа — JSON-список вида:
            {{"вопрос": "...", "ответ": "ДА/НЕТ", "рекомендация": "..."}}

            Текст рекламы:
            {ad_text}

            Вопросы:
            {list(QUESTIONS_TO_ARTICLES.keys())}
        """


def get_questions_answers(ad_text: str) -> list:
    """
    Классификация нарушений в тексте рекламы по вопросам
    :param ad_text: текст рекламы
    :return: list вида [{"вопрос": "...", "ответ": "ДА/НЕТ", "рекомендация": "..."}]
    """

    # Отправка запроса
    response = client.chat.completions.create(
        model=os.environ["MODEL"],
        messages=[
            {
                "role": "user",
                "content": form_prompt(ad_text)
            }
        ],
    )

    # Очистка ответа
    json_answers = response.choices[0].message.content
    json_answers = re.sub(r"^```json\s*|\s*```$", "", json_answers.strip())

    # Преобразование в list
    try:
        data = json.loads(json_answers)
    # Ошибка преобразования в json
    except json.JSONDecodeError:
        return []

    # Убираем некорректные вопросы
    correct_data = []
    for item in data:
        if all(k in item for k in ("вопрос", "ответ", "рекомендация")) \
                and item['вопрос'] in QUESTIONS_TO_ARTICLES:
            correct_data.append(item)
    return correct_data


def check_legislation(ad_text: str) -> list:
    """
    Поиск нарушений 5 статьи ФЗ в тексте рекламы
    :param ad_text: текст рекламы
    :return: list - список нарушений вида ["N часть 5 статьи ФЗ": {
                "text": "текст N части 5 статьи ФЗ",
                "recommendations": "сгенерированные рекомендации",
                "judicial_proceedings": "сопутствующие дела из судебной практики"
            }]
    """

    # Получаем ответы на вопросы от LLM
    data = get_questions_answers(ad_text)

    # Реклама правильная / Не удалось распознать ответ LLM
    if not data:
        return []

    # Формируем список рекомендаций для каждой части ФЗ
    article_to_recs = defaultdict(list)
    for item in data:
        # Отбираем только нарушения
        if item["ответ"] == "ДА":
            question = item["вопрос"]
            article = QUESTIONS_TO_ARTICLES.get(question)
            if article:
                article_to_recs[article].append(item["рекомендация"])

    # Формируем итоговую структуру
    result = []
    for article, recs in article_to_recs.items():
        # Получаем текст части 5 статьи ФЗ
        violation_text = ARTICLES_TO_VIOLATION_TEXT.get(article)
        # Получаем судебную практику по этой части 5 статьи ФЗ
        judicial_proceedings = CASES_BY_ARTICLE.get(article)
        # Объединяем рекомендации
        recs = ' '.join(recs)
        result.append({
            article: {
                "text": violation_text,
                "recommendations": recs,
                "judicial_proceedings": judicial_proceedings
            }
        })

    return result

