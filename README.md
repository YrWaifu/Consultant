### Запуск
```bash
cp .env.example .env
npm install
npm i -D @tailwindcss/cli
npm run tw:dev или npm run tw:build
docker compose up --build
```

### Если `npm i -D @tailwindcss/cli` не работает
```bash
npm cache clean --force  
```

### Как посмотреть варианты отчетов (по степени соответствия закону)
- Плохая: http://localhost:8000/v2/report?case=bad
- Средняя: http://localhost:8000/v2/report?case=medium
- Идеальная: http://localhost:8000/v2/report?case=good