from .classifiers import classify_alcohol_claims


def analyze_text(text: str) -> dict:
    return {"alcohol": classify_alcohol_claims(text)}


def analyze_media(path: str) -> dict:
    # TODO: OCR/CLIP/детекция маркировки 18+
    return {"ocr": {"text": "", "confidence": 0.0}}