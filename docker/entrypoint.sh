#!/bin/bash
set -e

echo "🔧 Ожидание доступности БД..."
sleep 3

echo "🗄️ Применение миграций..."
python manage.py db upgrade || echo "⚠️ Миграции не применились (возможно, уже применены)"

echo "🚀 Запуск приложения..."
exec "$@"

