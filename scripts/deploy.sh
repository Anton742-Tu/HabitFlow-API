#!/bin/bash
# Скрипт для ручного деплоя на сервер

set -e

echo "🚀 Запуск деплоя HabitFlow API..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка наличия необходимых файлов
check_files() {
    echo -e "${YELLOW}1. Проверка файлов...${NC}"

    local required_files=(
        "requirements.txt"
        "manage.py"
        ".env"
    )

    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            echo -e "${RED}❌ Отсутствует файл: $file${NC}"
            return 1
        fi
    done

    echo -e "${GREEN}✅ Все необходимые файлы на месте${NC}"
    return 0
}

# Проверка зависимостей
check_dependencies() {
    echo -e "\n${YELLOW}2. Проверка зависимостей...${NC}"

    # Проверка Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 не установлен${NC}"
        return 1
    fi

    # Проверка pip
    if ! command -v pip3 &> /dev/null; then
        echo -e "${RED}❌ pip3 не установлен${NC}"
        return 1
    fi

    # Проверка PostgreSQL
    if ! command -v psql &> /dev/null; then
        echo -e "${YELLOW}⚠️ PostgreSQL не установлен (пропускаем)${NC}"
    fi

    echo -e "${GREEN}✅ Зависимости проверены${NC}"
    return 0
}

# Проверка базы данных
check_database() {
    echo -e "\n${YELLOW}3. Проверка базы данных...${NC}"

    if [ -f ".env" ]; then
        source .env
    fi

    # Проверка подключения к PostgreSQL
    if command -v psql &> /dev/null && [ -n "$POSTGRES_HOST" ]; then
        if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1;" &> /dev/null; then
            echo -e "${GREEN}✅ База данных доступна${NC}"
        else
            echo -e "${RED}❌ Не удалось подключиться к базе данных${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️ Пропускаем проверку БД (SQLite или нет psql)${NC}"
    fi

    return 0
}

# Применение миграций
run_migrations() {
    echo -e "\n${YELLOW}4. Применение миграций...${NC}"

    if python manage.py migrate --noinput; then
        echo -e "${GREEN}✅ Миграции применены${NC}"
    else
        echo -e "${RED}❌ Ошибка применения миграций${NC}"
        return 1
    fi

    return 0
}

# Сборка статических файлов
collect_static() {
    echo -e "\n${YELLOW}5. Сборка статических файлов...${NC}"

    if python manage.py collectstatic --noinput --clear; then
        echo -e "${GREEN}✅ Статические файлы собраны${NC}"
    else
        echo -e "${RED}❌ Ошибка сбора статических файлов${NC}"
        return 1
    fi

    return 0
}

# Проверка приложения
check_application() {
    echo -e "\n${YELLOW}6. Проверка приложения...${NC}"

    if python manage.py check --deploy; then
        echo -e "${GREEN}✅ Проверка приложения пройдена${NC}"
    else
        echo -e "${RED}❌ Ошибка проверки приложения${NC}"
        return 1
    fi

    return 0
}

# Запуск тестов
run_tests() {
    echo -e "\n${YELLOW}7. Запуск тестов...${NC}"

    local test_result=0

    # Быстрые тесты
    if python manage.py test --failfast; then
        echo -e "${GREEN}✅ Тесты пройдены${NC}"
    else
        echo -e "${RED}❌ Тесты не пройдены${NC}"
        test_result=1
    fi

    return $test_result
}

# Перезапуск сервисов
restart_services() {
    echo -e "\n${YELLOW}8. Перезапуск сервисов...${NC}"

    # Проверяем какие сервисы доступны
    if systemctl list-unit-files | grep -q gunicorn; then
        echo -e "${YELLOW}Перезапуск Gunicorn...${NC}"
        if sudo systemctl restart gunicorn; then
            echo -e "${GREEN}✅ Gunicorn перезапущен${NC}"
        else
            echo -e "${RED}❌ Ошибка перезапуска Gunicorn${NC}"
            return 1
        fi
    fi

    if systemctl list-unit-files | grep -q nginx; then
        echo -e "${YELLOW}Перезагрузка Nginx...${NC}"
        if sudo systemctl reload nginx; then
            echo -e "${GREEN}✅ Nginx перезагружен${NC}"
        else
            echo -e "${RED}❌ Ошибка перезагрузки Nginx${NC}"
            return 1
        fi
    fi

    return 0
}

# Проверка работоспособности
health_check() {
    echo -e "\n${YELLOW}9. Проверка работоспособности...${NC}"

    # Даем время на запуск
    sleep 2

    # Проверяем доступность приложения
    if curl -s http://localhost:8000/api/ | grep -q "HabitFlow"; then
        echo -e "${GREEN}✅ Приложение работает${NC}"
    else
        echo -e "${RED}❌ Приложение не отвечает${NC}"
        return 1
    fi

    return 0
}

# Основной процесс деплоя
main() {
    echo "========================================"
    echo "     Деплой HabitFlow API"
    echo "========================================"

    local step=1
    local total_steps=9

    # Выполняем все шаги
    for step_func in check_files check_dependencies check_database \
                     run_migrations collect_static check_application \
                     run_tests restart_services health_check; do
        echo -e "\n${YELLOW}[Шаг $step/$total_steps]${NC}"

        if ! $step_func; then
            echo -e "${RED}❌ Деплой прерван на шаге: $step_func${NC}"
            exit 1
        fi

        ((step++))
    done

    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}🎉 Деплой успешно завершен!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "📊 Статистика:"
    echo "  • Время: $(date)"
    echo "  • Версия: $(git rev-parse --short HEAD)"
    echo "  • Файлы: $(find . -type f -name "*.py" | wc -l) Python файлов"
    echo ""
    echo "🌐 Приложение доступно по адресу:"
    echo "  • API: http://localhost:8000/api/"
    echo "  • Админка: http://localhost:8000/admin/"
    echo "  • Документация: http://localhost:8000/docs/"
}

# Запуск с обработкой ошибок
if main; then
    exit 0
else
    exit 1
fi
