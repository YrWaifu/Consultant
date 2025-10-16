import mimetypes
from ml.classifiers import analyze_text, analyze_audio


def run_ml(text: str | None, media_path: str | None):
    out = {}
    if text:
        out["text"] = analyze_text(text)
    if media_path:
        # TODO: передача аудио в ml модуль
        # Всё же временно сохраняется файл? Если нет, то можно передавать аудио в байтах
        with open(media_path, "rb") as f:
            data = f.read()
        audio_type = mimetypes.guess_type(media_path)[0]
        out["media"] = analyze_audio(data, audio_type)
    return out
