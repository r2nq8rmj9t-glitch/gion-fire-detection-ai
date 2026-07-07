#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip

# PyTorchはCPU専用版を先に入れる。
# 通常版はGPU用の巨大ファイル込みで、無料サーバーには重すぎるため。
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

pip install -r requirements.txt

# 画像分類用の軽量ランタイム（TensorFlowの代わり）。
# 注意: 旧「tflite-runtime」は2023年で更新停止しており、
# 新しい形式のTFLiteモデルを読めないため、必ず削除する。
# 代わりに更新が続いている公式の「ai-edge-litert」を使う。
pip uninstall -y tflite-runtime || true
pip install ai-edge-litert

# opencv共倒れ問題の修正:
# ultralyticsがGUI版opencvを勝手に入れるため、
# 一度「両方」消してから、サーバー用のheadless版だけを入れ直す
pip uninstall -y opencv-python opencv-python-headless || true
pip install --no-cache-dir opencv-python-headless

python manage.py collectstatic --no-input
python manage.py migrate
