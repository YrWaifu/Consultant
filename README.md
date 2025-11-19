# ИИ-модератор рекламы

Проверка рекламы на соответствие ФЗ «О рекламе» (38-ФЗ).

## 🚀 Быстрый деплой на сервере

**Обычное обновление** (сохраняет данные):
```bash
docker compose down && docker compose up -d --build
```

**Полная пересборка** (если что-то сломалось):
```bash
docker compose down
docker builder prune -a -f 
docker compose build --no-cache
docker compose up -d
```

**Мониторинг системы**:
```bash
./monitor.sh  # Показывает статус всех сервисов
```

✅ **Автовосстановление**: Воркеры и сервисы автоматически перезапускаются при сбоях  
✅ **Health Checks**: Система сама следит за здоровьем компонентов  
✅ **Сохранение данных**: Вся информация в защищенных Docker volumes  

**Стек**: FastAPI, PostgreSQL, Redis, RQ, Alembic, Tailwind CSS

---

## Запуск

```bash
# Установка
npm install 
cp .env.example .env

# Запуск (миграции применяются автоматически)
docker-compose up --build

# Первичная загрузка закона (опционально, 5-10 мин)
python manage.py parse-law

# Ручной запуск парсера
docker-compose exec api python manage.py parse-law

# Ручное добавление статей
docker-compose exec api python manage.py add-articles 

# Очистить кеш редиса
docker-compose exec redis redis-cli FLUSHALL

# Пример очистки бд 
docker-compose exec db psql -U postgres -d adlaw -c "DELETE FROM law_articles; DELETE FROM law_chapters; DELETE FROM law_versions;"   

# Удаление статей
docker-compose exec db psql -U postgres -d adlaw -c "DELETE FROM articles; DELETE FROM article_categories;"
```

Открыть: http://localhost:8000

---

## Основные команды

```bash
# Миграции
python manage.py db upgrade          # Применить
python manage.py db migrate "text"   # Создать новую

# Парсинг закона (автоматически каждый день в 03:00)
python manage.py parse-law

# CSS (разработка)
npm run tw:dev
```

---

## Архитектура

### Автоматический парсинг закона
- **Откуда**: КонсультантПлюс (https://consultant.ru/document/cons_doc_LAW_58968/)
- **Когда**: Каждый день в 03:00 (RQ Scheduler)
- **Куда**: PostgreSQL (таблицы `law_versions`, `law_articles`, `law_chapters`)
- **Код**: `backend/app/services/law_parser.py`

### Миграции БД
- **Система**: Alembic
- **Применение**: Автоматически при `docker-compose up` (через entrypoint.sh)
- **Версионирование**: `backend/app/migrations/versions/`

### Фоновые задачи
- **Технология**: RQ Worker + Redis
- **ML-анализ**: Выполняется асинхронно (не блокирует API)
- **Планировщик**: RQ Scheduler для cron-задач

---

## Структура БД

```
law_versions        # Версии закона с датами
├── law_articles    # Статьи (для проверки нарушений)
└── law_chapters    # Главы (структура закона)

users               # Пользователи
checks              # История проверок рекламы

articles            # Статьи от юристов
article_categories  # Категории статей от юристов
```

**Важно**: Каждая проверка привязана к версии закона на дату проверки (юридическая корректность).

---

## Примеры

```bash
# Отчеты
http://localhost:8000/v2/report?case=bad
http://localhost:8000/v2/report?case=medium
http://localhost:8000/v2/report?case=good

# API документация
http://localhost:8000/docs

# Админские маршруты
GET /admin/articles - админ-панель
POST /admin/articles/upload-json - загрузка JSON файла
POST /admin/articles/create-sample - создание примеров
GET /admin/articles/load-from-dir - загрузка из директории

# Проверка БД
docker-compose exec db psql -U postgres -d adlaw
SELECT * FROM law_versions;
```

---

## Решение проблем

```bash
# Пересоздать БД
docker-compose down -v
docker-compose up

# npm проблемы
npm cache clean --force

# Логи
docker-compose logs -f api
docker-compose logs -f worker
```