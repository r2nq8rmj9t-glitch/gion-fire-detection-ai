#!/usr/bin/env bash
set -o errexit

# 依存ライブラリのインストール
# （Build Command を ./build.sh にする場合、ここで必ず入れる）
pip install --upgrade pip
pip install -r requirements.txt

# ultralytics が opencv-python（GUI版）を連れてくることがあるため、
# サーバー用の headless 版に必ず入れ替える。
# これをしないと Render で「libGL.so.1 が無い」エラーで落ちる。
pip uninstall -y opencv-python || true
pip install opencv-python-headless

# 静的ファイル収集とDBマイグレーション
python manage.py collectstatic --no-input
python manage.py migrate
