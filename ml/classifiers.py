import os
import json
import re
import requests
from huggingface_hub import InferenceClient
from collections import defaultdict

from dictionaries import *

"""
Модуль поиска нарушений в текстовой рекламе
"""


def form_prompt(ad_text: str) -> str:
    """
    Формирует промпт
    :param ad_text: текст рекламы
    :return: str - текст запроса к LLM
    """

    return f'''
        Ты — эксперт по законодательству о рекламе Российской Федерации. Проанализируй текст рекламы и ответь на каждый вопрос строго «ДА» или «НЕТ». 
        Если ответ «ДА», обязательно добавь краткую рекомендацию, как устранить нарушение. Если нарушение отсутствует, ответь «НЕТ» без рекомендации.
        Руководствуйся пояснениями к каждому вопросу, чтобы не путать похожие вопросы. Обрати внимание, что есть вопросы на одну тему, но в каждом вопросе своя специфика.
        Формат ответа — JSON-список вида: {{"номер вопроса": "int", "ответ": "ДА/НЕТ", "рекомендация": "..."}}
        Текст рекламы: {ad_text}
        Вопросы с пояснениями: {' '.join([f'{n}. {q_text}' for n, q_text in QUESTIONS.items()])}
    '''


def get_questions_answers(ad_text: str) -> list:
    """
    Классификация нарушений в тексте рекламы по вопросам
    :param ad_text: текст рекламы
    :return: list вида [{"номер вопроса": "...", "ответ": "ДА/НЕТ", "рекомендация": "..."}]
    """

    client = InferenceClient(
        token=os.environ["HF_TOKEN"]
    )

    # Отправка запроса
    response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
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
        if all(k in item for k in ("номер вопроса", "ответ", "рекомендация")) \
                and item['номер вопроса'] in QUESTIONS:
            correct_data.append(item)
    return correct_data


def analyze_text(ad_text: str) -> list:
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
            question = item["номер вопроса"]
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


def analyze_audio(audio: bytes, mime_type: str) -> list:
    """
    Поиск нарушений 5 статьи ФЗ в аудио рекламе
    :param audio: аудио в байтах
    :param mime_type: тип аудио ('audio/mpeg', 'audio/flac', 'audio/wav' или другой)
    :return: list - список нарушений вида ["N часть 5 статьи ФЗ": {
                "text": "текст N части 5 статьи ФЗ",
                "recommendations": "сгенерированные рекомендации",
                "judicial_proceedings": "сопутствующие дела из судебной практики"
            }]
    """
    assert mime_type in ['audio/mpeg', 'audio/flac', 'audio/wav', 'audio/webm', 'audio/ogg', 'audio/mp4', 'audio/m4a',
                         'audio/amr'], ValueError('got incorrect audio type')

    headers = {
        "Authorization": f"Bearer {os.environ['HF_TOKEN']}",
    }

    response = requests.post(os.environ["AUDIO_API_URL"], headers={"Content-Type": mime_type, **headers}, data=audio)

    # Преобразование в json
    try:
        response = response.json()
    # Ошибка преобразования в json
    except json.JSONDecodeError:
        print('Could not convert to json response from HF')
        return []

    ad_text = response['text']
    return analyze_text(ad_text)
