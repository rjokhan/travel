#!/usr/bin/env bash
# ===== A CLUB TRAVEL — deploy.sh =====
# Безопасный деплой Django-проекта под systemd (service: travel.service)

set -Eeuo pipefail

SERVICE_NAME="travel.service"      # systemd unit
PY_BIN="python3"                   # системный python на сервере
REQUIREMENTS_FILE="requirements.txt"

# Переходим в директорию скрипта (корень проекта)
cd "$(dirname "$0")"

log() { printf "\n[\033[1;35mDEPLOY\033[0m] %s\n" "$*"; }
die() { printf "\n[\033[1;31mERROR\033[0m] %s\n\n" "$*" ; exit 1; }

log "Папка проекта: $(pwd)"

# 1) Git pull (если это git-репозиторий)
if [ -d ".git" ]; then
  log "Обновляю репозиторий (git pull)…"
  git pull --ff-only || die "git pull не удался"
else
  log "Git репозиторий не найден — пропускаю git pull"
fi

# 2) Подготовка виртуального окружения
if [ ! -d "venv" ]; then
  log "Создаю venv…"
  $PY_BIN -m venv venv || die "Не удалось создать venv"
fi
# shellcheck disable=SC1091
source venv/bin/activate
log "Python: $(python -V)"
python -m pip install --upgrade pip wheel

# 3) Установка зависимостей (если есть requirements.txt)
if [ -f "$REQUIREMENTS_FILE" ]; then
  log "Устанавливаю зависимости из $REQUIREMENTS_FILE…"
  pip install -r "$REQUIREMENTS_FILE"
else
  log "requirements.txt не найден — пропускаю установку зависимостей"
fi

# 4) Проверки и миграции
log "Проверяю проект (manage.py check)…"
python manage.py check || die "manage.py check выдал ошибку"

log "Применяю миграции…"
python manage.py migrate --noinput

# 5) Статика
log "Собираю статику…"
python manage.py collectstatic --noinput

# 6) Опционально — компиляция сообщений/локали (раскомментируйте при необходимости)
# log "Компилирую локали…"
# python manage.py compilemessages

# 7) Перезапуск сервиса
log "Перезапускаю systemd сервис: ${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"

# 8) Краткий статус
sleep 1
sudo systemctl status "${SERVICE_NAME}" --no-pager || die "Сервис ${SERVICE_NAME} не поднялся"

log "ГОТОВО ✅"
