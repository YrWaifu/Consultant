from ml.classifiers import analyze_text, analyze_audio


def run_ml(text: str | None, audio_bytes: bytes | None, audio_content_type: str | None):
    out = {}
    recognized_text = None
    
    if text:
        out["text"] = analyze_text(text)
        recognized_text = text
    elif audio_bytes and audio_content_type:
        # Передаем аудио в байтах напрямую в ml модуль
        # Получаем распознанный текст из аудио
        recognized_text = _get_transcribed_text_from_audio(audio_bytes, audio_content_type)
        if recognized_text:
            out["text"] = analyze_text(recognized_text)
    
    # Сохраняем распознанный текст для отображения на странице результата
    if recognized_text:
        out["recognized_text"] = recognized_text
    
    return out


def _get_transcribed_text_from_audio(audio_bytes: bytes, audio_content_type: str) -> str | None:
    """
    Распознает текст из аудио файла.
    Возвращает распознанный текст или None в случае ошибки.
    """
    try:
        import os
        import requests
        import json
        
        headers = {
            "Authorization": f"Bearer {os.environ.get('HF_TOKEN', '')}",
        }
        
        response = requests.post(
            os.environ.get("AUDIO_API_URL", ""),
            headers={"Content-Type": audio_content_type, **headers},
            data=audio_bytes
        )
        
        # Преобразование в json
        try:
            response_data = response.json()
            return response_data.get('text', None)
        except json.JSONDecodeError:
            print('Could not convert to json response from HF')
            return None
    except Exception as e:
        print(f"Ошибка при распознавании аудио: {e}")
        return None
