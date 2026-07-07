#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# opencv共倒れ問題の修正:
# ultralyticsがGUI版opencvを勝手に入れて、削除時にcv2が壊れるため、
# 一度「両方」消してから、headless版だけをクリーンに入れ直す
pip uninstall -y opencv-python opencv-python-headless || true
pip install --no-cache-dir opencv-python-headless

python manage.py collectstatic --no-input
python manage.py migrate
