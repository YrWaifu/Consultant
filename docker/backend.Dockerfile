FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Зависимости
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Код
COPY backend/ backend/
COPY ml/ ml/
ENV PYTHONPATH=/app

# Запуск
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]