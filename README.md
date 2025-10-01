### Запуск
cp .env.example .env
npm install
npm i -D @tailwindcss/cli
npm run tw:dev или npm run tw:build
docker compose up --build


### Точки входа
- GET / — форма проверки
- POST /api/checks/ — запуск проверки (JSON, HTMX)
- GET /history — история проверок (позже)
- POST /api/search/ — поиск по базе знаний (laws.json)

### Как посмотреть варианты отчетов
- Плохая: http://localhost:8000/v2/report?case=bad
- Средняя: http://localhost:8000/v2/report?case=medium
- Идеальная: http://localhost:8000/v2/report?case=good