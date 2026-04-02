#!/bin/bash
# Скрипт деплоя на сервер 94.198.218.56
# Запускать локально: bash deploy.sh

set -e

SERVER="root@94.198.218.56"
REMOTE_DIR="/opt/vesnaidet"

echo "==> Копируем файлы на сервер..."
rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='vesnaidet.db' \
  ./ "$SERVER:$REMOTE_DIR/"

echo "==> Запускаем на сервере..."
ssh "$SERVER" << 'ENDSSH'
  cd /opt/vesnaidet

  # Nginx конфиг
  cp nginx.conf /etc/nginx/sites-available/vesnaidet
  ln -sf /etc/nginx/sites-available/vesnaidet /etc/nginx/sites-enabled/vesnaidet
  nginx -t && systemctl reload nginx

  # Docker
  docker compose pull || true
  docker compose up -d --build

  echo "==> Готово! Сайт доступен на http://vesnaidet.ru"
ENDSSH
