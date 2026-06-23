#!/usr/bin/env bash
# ResumeForge — pull latest and update the running service on the VPS.
# Usage (from the project root):  ./deploy/deploy.sh
set -euo pipefail

cd "$(dirname "$0")/.."   # project root
echo "==> Project: $(pwd)"

echo "==> Pulling latest from git"
git pull --ff-only

echo "==> Activating venv + installing deps"
source .venv/bin/activate
pip install -q -r requirements.txt

echo "==> Ensuring headless Chromium (for PDF/PNG export)"
python -m playwright install chromium

echo "==> Migrating database"
python manage.py migrate --noinput

echo "==> Collecting static files"
python manage.py collectstatic --noinput

echo "==> Restarting service"
sudo systemctl restart resumeforge

echo "==> Done."
sudo systemctl --no-pager status resumeforge | head -6
