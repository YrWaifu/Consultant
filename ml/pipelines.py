from ml.classifiers import check_legislation


def analyze_text(text: str) -> list:
    """
    Поиск нарушений 5 статьи ФЗ в тексте рекламы
    :param text: текст рекламы
    :return: list - список нарушений вида ["N часть 5 статьи ФЗ": {
                "text": "текст N части 5 статьи ФЗ",
                "recommendations": "сгенерированные рекомендации",
                "judicial_proceedings": "сопутствующие дела из судебной практики"
            }]
    """
    return check_legislation(text)


def analyze_media(path: str) -> dict:
    # TODO
    return {"ocr": {"text": "", "confidence": 0.0}}