# UPPETIT Promo Bot

Telegram-бот для совместной промо-акции [UPPETIT](https://uppetit.ru) и городского медиа [ЩУКА](https://thepike.ru/).

Бот выдаёт уникальные QR-коды на подарки от UPPETIT участникам акции, привлечённым через медиа ЩУКА.

## Возможности

- Проверка подписки на канал перед выдачей подарка
- Выдача уникальных QR-кодов (один раз на пользователя)
- Повторная выдача подарка по решению администратора
- Защита от race conditions при параллельных запросах
- Временные рамки акции
- Admin-панель для управления и статистики
- Асинхронная работа с БД (PostgreSQL)
- Структурированное логирование
- Production-ready

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
CHANNEL_USERNAME=@uppetit_info
LOG_LEVEL=INFO
EOF
```

Получить токен: [@BotFather](https://t.me/BotFather)
Узнать свой ID: [@userinfobot](https://t.me/userinfobot)

### 3. База данных

```bash
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
│   ├── handlers/
│   │   ├── start.py   # /start, /my_id + callback проверки подписки
│   │   └── admin.py   # /stats, /show_info, /show_users, /new_codes,
│   │                  # /add_another_qr, /delete_code,
│   │                  # /add_admin, /delete_admin, /cancel
│   ├── services/      # Бизнес-логика (user, promo, qr, admin)
│   ├── database/      # SQLAlchemy модели и сессии
│   ├── middleware/    # DB session middleware
│   ├── utils/         # Логирование и утилиты
│   ├── config.py      # Конфигурация из .env
│   ├── bot.py         # Инициализация бота и dispatcher
│   └── main.py        # Точка входа
├── alembic/           # Миграции БД
├── tools/             # CLI инструменты (import_codes)
└── requirements.txt
```

## Использование

### Для пользователей

1. **Получить промокод:**
   - Отправить `/start` боту
   - Если не подписан на [@uppetit_info](https://t.me/uppetit_info) — бот попросит подписаться и покажет кнопки «Подписаться на канал» и «Я подписался ✅»
   - После подтверждения подписки — получить приветствие и QR-код с промокодом
   - При повторном запросе: "Вы уже получили подарок"

2. **Узнать свой Telegram ID:**
   - Отправить `/my_id` боту
   - Бот покажет ваш ID, имя и username

### Для администраторов

**Статистика промокодов:**
```
/stats
```
Показывает: всего кодов, доступно, выдано.

**Детальная информация:**
```
/show_info
```
Показывает количество кодов (всего / выдано / в запасе) и количество уникальных пользователей.

**Список пользователей:**
```
/show_users
```
Показывает список всех пользователей бота: Telegram ID, имя, username, дата регистрации.

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

**Удалить код:**
```
/delete_code
```
Запрашивает код для удаления. Бот находит его в базе, показывает статус (`доступен` / `выдан пользователю`) и предлагает подтвердить удаление через inline-кнопки. Действие необратимо.

**Разрешить пользователю получить ещё один подарок:**
```
/add_another_qr
```
Показывает список пользователей, которые уже получили подарок. Нажатие на пользователя выдаёт ему разрешение на получение ещё одного QR-кода. При следующем `/start` бот выдаст новый подарок и автоматически снимет разрешение.

**Добавить админа:**
```
/add_admin
```
Запрашивает Telegram ID нового админа. Только текущие админы могут добавлять новых.

**Удалить админа:**
```
/delete_admin
```
Показывает inline-кнопки с именами админов для удаления. Главный админ не может быть удалён.

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
#   app/ alembic/ tools/ requirements.txt alembic.ini
# scp /tmp/bot.tar.gz root@your-server-ip:/opt/bots/uppetit-bot/
#
# Затем на СЕРВЕРЕ распаковать:
# tar xzf bot.tar.gz && rm bot.tar.gz

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
CHANNEL_USERNAME=@uppetit_info
LOG_LEVEL=INFO
EOF

# 8. Применить миграции
alembic upgrade head

# 9. Импортировать промокоды
python -m tools.import_codes --file codes.txt

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
systemctl stop uppetit-bot

cd /opt/bots/uppetit-bot
# Скопировать новые файлы (см. шаг 5 выше)

source .venv/bin/activate
pip install --upgrade -r requirements.txt
alembic upgrade head

systemctl start uppetit-bot
```

## Архитектура

### Слои приложения

```
┌──────────────────────────────────────────┐
│   Handlers (Telegram)                    │
│   start.py  — /start, /my_id            │
│   admin.py  — управление кодами и БД    │
├──────────────────────────────────────────┤
│   Services (Business Logic)              │
│   user, promo, qr, admin                │
├──────────────────────────────────────────┤
│   Database (SQLAlchemy + asyncpg)        │
├──────────────────────────────────────────┤
│   PostgreSQL                             │
└──────────────────────────────────────────┘
```

### Модели данных

**User:**
- id, telegram_id (unique), username, first_name, last_name
- created_at, last_seen_at
- extra_gift_allowed (bool) — флаг разрешения на повторный подарок

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
grep BOT_TOKEN .env
```

### Ошибка "permission denied for schema public"

```bash
sudo -u postgres psql -d uppetit_promo_bot << EOF
GRANT ALL ON SCHEMA public TO uppetit;
ALTER DATABASE uppetit_promo_bot OWNER TO uppetit;
\q
EOF
```

### Бот не проверяет подписку / все получают подарок без подписки

Бот должен быть **администратором** канала `@uppetit_info`. Без этого Telegram API не позволяет проверять статус участников — при ошибке бот пропускает проверку (fail open), чтобы не блокировать пользователей.

1. Откройте канал в Telegram → Управление каналом → Администраторы
2. Добавьте бота как администратора (достаточно минимальных прав)
3. Убедитесь, что `CHANNEL_USERNAME=@uppetit_info` задан в `.env`

### "Все подарки разобрали" (но коды есть)

```bash
# Проверить коды в БД
sudo -u postgres psql -d uppetit_promo_bot -c "SELECT status, COUNT(*) FROM promo_codes GROUP BY status;"

# Если кодов нет — импортировать
cd /opt/bots/uppetit-bot
source .venv/bin/activate
python -m tools.import_codes --file codes.txt

systemctl restart uppetit-bot
```

## Миграции

```bash
# Применить все
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

## Лицензия

Проприетарный код. Разработан для совместной промо-акции UPPETIT и городского медиа ЩУКА.
