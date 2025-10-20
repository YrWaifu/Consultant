from ml.classifiers import analyze_text, analyze_audio


def run_ml(text: str | None, audio_bytes: bytes | None, audio_content_type: str | None):
    out = {}
    if text:
        out["text"] = analyze_text(text)
    if audio_bytes and audio_content_type:
        # Передаем аудио в байтах напрямую в ml модуль
        out["text"] = analyze_audio(audio_bytes, audio_content_type)
    return out
