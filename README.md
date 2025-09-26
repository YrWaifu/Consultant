### Запуск
cp .env.example .env
make up # или docker compose up --build


### Точки входа
- GET / — форма проверки
- POST /api/checks/ — запуск проверки (JSON, HTMX)
- GET /history — история проверок (позже)
- POST /api/search/ — поиск по базе знаний (laws.json)


### Где менять логику
- `services/rules.py` — регулярки/правила
- `ml/` — модели и пайплайны
- `services/reporting.py` — экспорт PDF/HTML