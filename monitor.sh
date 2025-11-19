#!/bin/bash

# 🎯 Скрипт мониторинга консультанта по рекламе
# Использование: ./monitor.sh

echo "🎯 === СТАТУС КОНСУЛЬТАНТА ПО РЕКЛАМЕ ==="
echo ""

# Проверка контейнеров
echo "📦 КОНТЕЙНЕРЫ:"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" | head -1
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" | grep -v NAME | while read line; do
    if echo "$line" | grep -q "Up.*health"; then
        echo "✅ $line"
    elif echo "$line" | grep -q "Up"; then
        echo "🔄 $line"
    else
        echo "❌ $line"
    fi
done
echo ""

# Проверка health status
echo "💚 HEALTH STATUS:"
for service in api worker db redis; do
    health=$(docker compose exec $service echo "OK" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "✅ $service: Healthy"
    else
        echo "❌ $service: Unhealthy"
    fi
done
echo ""

# Проверка очередей Redis
echo "📋 ОЧЕРЕДИ ЗАДАЧ:"
checks_queue=$(docker compose exec redis redis-cli LLEN rq:queue:checks 2>/dev/null || echo "N/A")
default_queue=$(docker compose exec redis redis-cli LLEN rq:queue:default 2>/dev/null || echo "N/A") 
failed_queue=$(docker compose exec redis redis-cli LLEN rq:queue:failed 2>/dev/null || echo "N/A")

echo "   📝 Очередь проверок: $checks_queue задач"
echo "   📋 Основная очередь: $default_queue задач"
echo "   ❌ Неудачные задачи: $failed_queue задач"
echo ""

# Последние логи воркера
echo "📰 ПОСЛЕДНИЕ ЛОГИ ВОРКЕРА:"
docker compose logs worker --tail=3 2>/dev/null | sed 's/^/   /'
echo ""

# Использование ресурсов
echo "💻 РЕСУРСЫ СЕРВЕРА:"
echo "   RAM: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
echo "   Диск: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 ")"}')"
echo ""

# Быстрые команды
echo "🛠️  БЫСТРЫЕ КОМАНДЫ:"
echo "   Перезапуск воркера:    docker compose restart worker"
echo "   Логи воркера:          docker compose logs -f worker"
echo "   Полный перезапуск:     docker compose down && docker compose up -d"
echo "   Очистка очередей:      docker compose exec redis redis-cli FLUSHDB"
echo ""

echo "✨ Мониторинг завершен!"
