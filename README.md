# UPPETIT Promo Bot

Telegram-бот для выдачи QR-кодов на подарки в сети UPPETIT.

## Возможности

- ✅ Выдача уникальных QR-кодов (один раз на пользователя)
- ✅ Защита от race conditions при параллельных запросах
- ✅ Временные рамки акции
- ✅ Admin-панель для управления и статистики
- ✅ Асинхронная работа с БД (PostgreSQL)
- ✅ Структурированное логирование
- ✅ Production-ready

## Быстрый старт (разработка)

### 1. Установка

```bash
# Создать виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

### 2. Настройка

```bash
# Создать .env файл
cat > .env << 'EOF'
BOT_TOKEN=your_bot_token_from_botfather
DATABASE_URL=sqlite+aiosqlite:///./promo_bot.db
ADMIN_IDS=your_telegram_id
PROMO_START=2026-02-05
PROMO_END=2026-05-30
LOG_LEVEL=INFO
EOF
```

Получить токен: [@BotFather](https://t.me/BotFather)
Узнать свой ID: [@userinfobot](https://t.me/userinfobot)

### 3. База данных

```bash
# Создать миграцию
alembic revision --autogenerate -m "Initial migration"

# Применить миграции
alembic upgrade head

# Добавить тестовые промокоды
python -m tools.import_codes --test
```

### 4. Запуск

```bash
python -m app.main
```

Бот готов к работе! Найдите его в Telegram и отправьте `/start`.

## Структура проекта

```
PromoBotShuka/
├── app/
│   ├── handlers/          # Обработчики команд (/start, /my_id, /stats, /new_codes, /show_info, /show_users, /add_admin, /delete_admin, /cancel)
│   ├── services/          # Бизнес-логика (user, promo, qr, admin)
│   ├── database/          # SQLAlchemy модели и сессии
│   ├── middleware/        # DB session middleware
│   ├── utils/             # Логирование и утилиты
│   ├── config.py          # Конфигурация из .env
│   ├── bot.py             # Инициализация бота и dispatcher
│   └── main.py            # Точка входа
├── alembic/               # Миграции БД
├── tools/                 # CLI инструменты (import_codes)
└── requirements.txt
```

## Использование

### Для пользователей

1. **Получить промокод:**
   - Отправить `/start` боту
   - Получить приветствие и QR-код с промокодом
   - При повторном запросе: "Вы уже получили подарок"

2. **Узнать свой Telegram ID:**
   - Отправить `/my_id` боту
   - Бот покажет ваш ID, имя и username

### Для администраторов

**Детальная информация:**
```
/show_info
```
Показывает:
- Количество кодов всего
- Количество выданных кодов
- Количество кодов в запасе
- Количество уникальных пользователей

**Список пользователей (новое):**
```
/show_users
```
Показывает список всех пользователей бота:
- Telegram ID
- Имя
- Username
- Дата регистрации

**Статистика промокодов:**
```
/stats
```
Показывает: всего кодов, доступно, выдано.

**Добавить админа:**
```
/add_admin
```
Запрашивает Telegram ID нового админа.
Только текущие админы могут добавлять новых.

**Удалить админа:**
```
/delete_admin
```
Показывает inline кнопки с именами админов для удаления.
Главный админ (ID: 854825784) не может быть удален.

**Добавить коды через Telegram:**
```
/new_codes
```
Запрашивает коды для добавления. Отправьте коды построчно:
```
987651527138080
987652589596192
987652691640275
```
Бот покажет сколько кодов добавлено и сколько пропущено (дубликаты).

**CLI импорт (альтернативный способ):**
```bash
# Из файла codes.txt (по одному коду на строку)
python -m tools.import_codes --file codes.txt

# Тестовые 5 кодов
python -m tools.import_codes --test
```

## Деплой на VPS

### Требования

- Ubuntu 24.04+
- Python 3.12
- PostgreSQL
- Root доступ

### Быстрая установка

```bash
# 1. Подключиться к серверу
ssh root@your-server-ip

# 2. Установить зависимости
apt update && apt upgrade -y
apt install -y python3.12-venv python3-pip postgresql postgresql-contrib

# 3. Настроить PostgreSQL
sudo -u postgres psql << EOF
CREATE DATABASE uppetit_promo_bot;
CREATE USER uppetit WITH PASSWORD 'secure_password';
ALTER DATABASE uppetit_promo_bot OWNER TO uppetit;
GRANT ALL ON SCHEMA public TO uppetit;
\q
EOF

systemctl start postgresql
systemctl enable postgresql

# 4. Создать директорию проекта
mkdir -p /opt/bots/uppetit-bot
cd /opt/bots/uppetit-bot

# 5. Скопировать файлы проекта на сервер
# Выполнить на ЛОКАЛЬНОЙ машине:
# cd /path/to/PromoBotShuka
# tar czf /tmp/bot.tar.gz --exclude='.venv' --exclude='.git' --exclude='__pycache__' \
#   app/ alembic/ tools/ requirements.txt alembic.ini docker-compose.yml Dockerfile
# scp /tmp/bot.tar.gz root@your-server-ip:/opt/bots/uppetit-bot/
#
# Затем на СЕРВЕРЕ распаковать:
# cd /opt/bots/uppetit-bot
# tar xzf bot.tar.gz
# rm bot.tar.gz

# 6. Установить Python зависимости
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 7. Создать .env файл
cat > .env << 'EOF'
BOT_TOKEN=your_bot_token
DATABASE_URL=postgresql+asyncpg://uppetit:secure_password@localhost:5432/uppetit_promo_bot
ADMIN_IDS=your_telegram_id
PROMO_START=2026-02-05
PROMO_END=2026-05-30
LOG_LEVEL=INFO
EOF

# 8. Применить миграции
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# 9. Импортировать промокоды
python -m tools.import_codes --test

# 10. Создать systemd service
cat > /etc/systemd/system/uppetit-bot.service << 'EOF'
[Unit]
Description=UPPETIT Promo Telegram Bot
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/bots/uppetit-bot
Environment="PATH=/opt/bots/uppetit-bot/.venv/bin"
ExecStart=/opt/bots/uppetit-bot/.venv/bin/python -m app.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 11. Запустить бота
systemctl daemon-reload
systemctl enable uppetit-bot
systemctl start uppetit-bot

# 12. Проверить статус
systemctl status uppetit-bot
journalctl -u uppetit-bot -f
```

### Управление ботом

```bash
# Статус
systemctl status uppetit-bot

# Логи в реальном времени
journalctl -u uppetit-bot -f

# Перезапуск
systemctl restart uppetit-bot

# Остановка
systemctl stop uppetit-bot
```

### Обновление бота

```bash
# Остановить
systemctl stop uppetit-bot

# Обновить код (git pull или скопировать файлы)
cd /opt/bots/uppetit-bot
# git pull  # если используете git

# Активировать окружение
source .venv/bin/activate

# Обновить зависимости
pip install --upgrade -r requirements.txt

# Применить миграции
alembic upgrade head

# Запустить
systemctl start uppetit-bot
```

### Docker деплой (альтернатива)

⚠️ **Примечание:** На некоторых серверах могут быть проблемы с доступом к репозиториям Docker при сборке. В таких случаях используйте systemd (см. выше).

```bash
# 1. Подключиться к серверу
ssh root@your-server-ip

# 2. Установить Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# 3. Создать директорию проекта
mkdir -p /opt/bots/uppetit-bot
cd /opt/bots/uppetit-bot

# 4. Скопировать файлы проекта (выполнить на локальной машине)
# cd /path/to/PromoBotShuka
# tar czf /tmp/bot.tar.gz --exclude='.venv' --exclude='.git' --exclude='__pycache__' \
#   app/ alembic/ tools/ requirements.txt alembic.ini docker-compose.yml Dockerfile .dockerignore
# scp /tmp/bot.tar.gz root@your-server-ip:/opt/bots/uppetit-bot/
#
# На сервере:
# cd /opt/bots/uppetit-bot
# tar xzf bot.tar.gz
# rm bot.tar.gz

# 5. Создать .env файл
cat > .env << 'EOF'
BOT_TOKEN=your_bot_token
DATABASE_URL=postgresql+asyncpg://uppetit:uppetit_password@postgres:5432/uppetit_promo_bot
ADMIN_IDS=your_telegram_id
PROMO_START=2026-02-05
PROMO_END=2026-05-30
LOG_LEVEL=INFO
EOF

# 6. Обновить docker-compose.yml (раскомментировать секцию bot)
# Убедитесь, что в docker-compose.yml секция bot активна:
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: uppetit_postgres
    environment:
      POSTGRES_USER: uppetit
      POSTGRES_PASSWORD: uppetit_password
      POSTGRES_DB: uppetit_promo_bot
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U uppetit"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  bot:
    build: .
    container_name: uppetit_bot
    depends_on:
      postgres:
        condition: service_healthy
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

volumes:
  postgres_data:
EOF

# 7. Запустить через Docker Compose
docker compose up -d --build

# 8. Проверить статус
docker compose ps
docker compose logs bot

# 9. Применить миграции (внутри контейнера)
docker compose exec bot alembic revision --autogenerate -m "Initial migration"
docker compose exec bot alembic upgrade head

# 10. Импортировать промокоды
docker compose exec bot python -m tools.import_codes --test

# 11. Проверить логи
docker compose logs -f bot
```

**Управление Docker ботом:**

```bash
# Статус контейнеров
docker compose ps

# Логи в реальном времени
docker compose logs -f bot

# Перезапуск
docker compose restart bot

# Остановка
docker compose down

# Полная остановка с удалением volumes
docker compose down -v

# Пересборка после изменений
docker compose up -d --build
```

**Обновление Docker бота:**

```bash
# Остановить
docker compose down

# Обновить код (скопировать новые файлы)

# Пересобрать и запустить
docker compose up -d --build

# Применить миграции
docker compose exec bot alembic upgrade head
```

## Архитектура

### Слои приложения

```
┌──────────────────────────────┐
│   Handlers (Telegram)        │  /start, /stats, /add_codes
├──────────────────────────────┤
│   Services (Business Logic)  │  user, promo, qr
├──────────────────────────────┤
│   Database (SQLAlchemy)      │  models, session
├──────────────────────────────┤
│   PostgreSQL                 │
└──────────────────────────────┘
```

### Модели данных

**User:**
- id, telegram_id (unique), username, first_name, last_name
- created_at, last_seen_at

**PromoCode:**
- id, raw_code (unique), status (AVAILABLE | ASSIGNED)
- assigned_to_user_id, assigned_at, created_at

**Admin:**
- id, telegram_id (unique), first_name, username
- created_at

### Защита от race conditions

Используется PostgreSQL блокировка:
```sql
SELECT * FROM promo_codes
WHERE status = 'AVAILABLE'
LIMIT 1
FOR UPDATE SKIP LOCKED;
```

Гарантирует: один код = один пользователь при параллельных запросах.

### Индексы БД

- `users.telegram_id` (unique)
- `admins.telegram_id` (unique)
- `promo_codes.raw_code` (unique)
- `promo_codes.status`
- `promo_codes.assigned_to_user_id`
- Композитный: `(status, assigned_to_user_id)`

## Troubleshooting

### Бот не отвечает

```bash
# Проверить статус
systemctl status uppetit-bot

# Проверить логи
journalctl -u uppetit-bot -n 50

# Проверить токен
cat .env | grep BOT_TOKEN
```

### Ошибка "permission denied for schema public"

```bash
sudo -u postgres psql -d uppetit_promo_bot << EOF
GRANT ALL ON SCHEMA public TO uppetit;
ALTER DATABASE uppetit_promo_bot OWNER TO uppetit;
\q
EOF
```

### Ошибка "ImportError: cannot import name 'close_db'"

Убедитесь, что в `app/database/__init__.py` есть:
```python
from .session import async_session_maker, init_db, close_db

__all__ = [
    "async_session_maker",
    "init_db",
    "close_db",
]
```

### "Все подарки разобрали" (но коды есть)

```bash
# Проверить коды в БД
sudo -u postgres psql -d uppetit_promo_bot -c "SELECT status, COUNT(*) FROM promo_codes GROUP BY status;"

# Если кодов нет - импортировать
cd /opt/bots/uppetit-bot
source .venv/bin/activate
python -m tools.import_codes --test

# Перезапустить бота
systemctl restart uppetit-bot
```

## Миграции

```bash
# Создать миграцию
alembic revision --autogenerate -m "Description"

# Применить
alembic upgrade head

# Откатить последнюю
alembic downgrade -1

# Текущая версия
alembic current

# История
alembic history
```

## Мониторинг

### Проверка статистики в БД

```bash
# Количество пользователей
sudo -u postgres psql -d uppetit_promo_bot -c "SELECT COUNT(*) FROM users;"

# Промокоды по статусам
sudo -u postgres psql -d uppetit_promo_bot -c "SELECT status, COUNT(*) FROM promo_codes GROUP BY status;"

# Последние пользователи
sudo -u postgres psql -d uppetit_promo_bot -c "SELECT telegram_id, username, created_at FROM users ORDER BY created_at DESC LIMIT 10;"
```

### Резервное копирование

```bash
# Создать бэкап
mkdir -p /opt/backups/uppetit-bot
sudo -u postgres pg_dump uppetit_promo_bot > /opt/backups/uppetit-bot/backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановить
systemctl stop uppetit-bot
sudo -u postgres psql uppetit_promo_bot < /opt/backups/uppetit-bot/backup_YYYYMMDD_HHMMSS.sql
systemctl start uppetit-bot
```

### Автоматический бэкап (crontab)

```bash
crontab -e

# Добавить:
0 3 * * * sudo -u postgres pg_dump uppetit_promo_bot > /opt/backups/uppetit-bot/backup_$(date +\%Y\%m\%d_\%H\%M\%S).sql
0 4 * * * find /opt/backups/uppetit-bot -name "backup_*.sql" -mtime +30 -delete
```

## Логирование

Structured logging с контекстом:
```python
logger.info(
    "QR code sent to user",
    telegram_id=user_telegram_id,
    user_id=user.id,
    code_id=promo_code.id,
    raw_code=promo_code.raw_code,
)
```

Все события логируются с метаданными для анализа.

## Безопасность

- ✅ Race condition защита через `FOR UPDATE SKIP LOCKED`
- ✅ Транзакционная целостность
- ✅ Admin команды только для `ADMIN_IDS`
- ✅ Валидация конфигурации при старте
- ✅ ORM защита от SQL Injection
- ✅ `.env` не в git
- ⚠️ Используйте сильные пароли для БД
- ⚠️ Настройте firewall на сервере
- ⚠️ Используйте SSH ключи вместо паролей

## Лицензия

Проприетарный код для UPPETIT.
