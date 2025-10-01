# тупая заглушка, чтобы не скучно было нажимать кнопку
from typing import Sequence

def analyze_ad(text: str | None, claims: Sequence[str] | None, file_name: str | None):
    messages = []
    if text and len(text) < 30:
        messages.append("Текст очень короткий, возможно неинформативен.")
    if claims:
        messages.append(f"Отмечено {len(claims)} утверждений — проверим соответствующие правила.")
    if file_name:
        messages.append(f"Файл «{file_name}» принят и будет обработан.")
    if not messages:
        messages.append("Данных почти нет, но заглушка уверенно делает вид, что работает.")
    return {"messages": messages}
