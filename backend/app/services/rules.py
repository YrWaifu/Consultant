import re, json, pathlib


BANNED_CLAIMS = [r"\bлучший\b", r"\bсамый\b", r"\bединственный\b", r"\bабсолютн"]


def load_laws():
    p = pathlib.Path(__file__).resolve().parents[1] / "knowledge" / "laws.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return []


def rule_based_check(text: str) -> list[dict]:
    issues = []
    for pat in BANNED_CLAIMS:
        if re.search(pat, text, flags=re.I):
            issues.append({
            "code": "claim.superlative",
            "title": "Запрещенные превосходные формулировки",
            "level": "medium",
            "evidence": pat,
            "fix": "Указать критерии оценки или убрать превосходную форму"
            })
    return issues