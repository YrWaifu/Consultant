from __future__ import annotations
from random import randint


def get_stats() -> dict:
    """Простая заглушка общей статистики аккаунта."""
    total = 142
    ok = 77
    warn = 41
    bad = 24
    last30 = [randint(5, 100) for _ in range(30)]
    return {
        "total_checks": total,
        "ok": ok,
        "warn": warn,
        "bad": bad,
        "last30": last30,
    }


