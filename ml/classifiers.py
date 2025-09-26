# Здесь будут реальные модели позже. Пока возвращаем фиктивные оценки.


def classify_alcohol_claims(text: str) -> dict:
    score = 0.7 if "алкоголь" in text.lower() else 0.1
    return {"risk": score, "label": "alcohol_promotion" if score > 0.5 else "ok"}