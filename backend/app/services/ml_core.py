from ml.pipelines import analyze_text, analyze_media


def run_ml(text: str | None, media_path: str | None):
    out = {}
    if text:
        out["text"] = analyze_text(text)
    if media_path:
        out["media"] = analyze_media(media_path)
    return out