FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Системные зависимости и шрифты с поддержкой кириллицы
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc curl xz-utils \
    fontconfig fonts-dejavu fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Установка Node.js через официальные бинарники
RUN curl -fsSL https://nodejs.org/dist/v18.19.0/node-v18.19.0-linux-x64.tar.xz | tar -xJ -C /usr/local --strip-components=1 \
    && ln -s /usr/local/bin/node /usr/bin/node \
    && ln -s /usr/local/bin/npm /usr/bin/npm

# Python зависимости
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Node.js зависимости и сборка CSS
COPY package.json ./
RUN npm install

COPY tailwind.config.js ./
COPY backend/app/static/css/app.css ./backend/app/static/css/app.css
COPY backend/app/templates/ ./backend/app/templates/

# Копируем остальные файлы бэкенда
COPY backend/ backend/
COPY ml/ ml/
COPY alembic.ini .
COPY manage.py .

# Сборка CSS (после копирования всех файлов)
RUN npm run tw:build

COPY docker/entrypoint.sh /entrypoint.sh
# Убедиться, что скрипт без CRLF и исполняемый
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

ENV PYTHONPATH=/app

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]