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
COPY alembic.ini .
COPY manage.py .
COPY docker/entrypoint.sh /entrypoint.sh
# Убедиться, что скрипт без CRLF и исполняемый
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

ENV PYTHONPATH=/app

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]