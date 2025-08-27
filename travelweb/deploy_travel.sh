#!/usr/bin/env bash
# ===== A CLUB TRAVEL — deploy_travel.sh (auto-detect manage.py) =====
set -Eeuo pipefail

SERVICE_NAME="travel.service"
PY_BIN="python3"
REQUIREMENTS_FILE="requirements.txt"

# Абсолютный путь к корню репозитория (где лежит этот скрипт)
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"

log() { printf "\n[\033[1;35mDEPLOY\033[0m] %s\n" "$*"; }
die() { printf "\n[\033[1;31mERROR\033[0m] %s\n\n" "$*" ; exit 1; }

log "REPO_ROOT: ${REPO_ROOT}"

# Где лежит manage.py
if [ -f "${REPO_ROOT}/manage.py" ]; then
  MANAGE_DIR="${REPO_ROOT}"
elif [ -f "${REPO_ROOT}/travelweb/manage.py" ]; then
  MANAGE_DIR="${REPO_ROOT}/travelweb"
else
  die "manage.py не найден ни в ${REPO_ROOT}, ни в ${REPO_ROOT}/travelweb"
fi
log "MANAGE_DIR: ${MANAGE_DIR}"

# venv всегда храним в корне репо
VENV_DIR="${REPO_ROOT}/venv"

# 1) git pull
if [ -d "${REPO_ROOT}/.git" ]; then
  log "git pull…"
  git -C "${REPO_ROOT}" pull --ff-only || die "git pull failed"
else
  log "Git репозиторий не найден — пропускаю pull"
fi

# 2) venv
if [ ! -d "${VENV_DIR}" ]; then
  log "Создаю venv…"
  "${PY_BIN}" -m venv "${VENV_DIR}" || die "venv create failed"
fi
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"
log "Python: $(python -V)"
python -m pip install --upgrade pip wheel

# 3) deps
if [ -f "${REPO_ROOT}/${REQUIREMENTS_FILE}" ]; then
  log "pip install -r ${REQUIREMENTS_FILE}…"
  pip install -r "${REPO_ROOT}/${REQUIREMENTS_FILE}"
else
  log "requirements.txt не найден — пропускаю установку зависимостей"
fi

# 4) Django команды — запускаем из папки с manage.py
cd "${MANAGE_DIR}"
log "manage.py check…"
python manage.py check || die "manage.py check failed"

log "migrate…"
python manage.py migrate --noinput

log "collectstatic…"
python manage.py collectstatic --noinput

# 5) restart
log "restart ${SERVICE_NAME}…"
sudo systemctl restart "${SERVICE_NAME}"
sleep 1
sudo systemctl status "${SERVICE_NAME}" --no-pager || die "service not running"

log "ГОТОВО ✅"
