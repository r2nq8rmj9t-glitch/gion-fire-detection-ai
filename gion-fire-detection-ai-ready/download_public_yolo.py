"""
公開されている火・煙検出YOLOモデルをダウンロードするためのスクリプトです。

このファイルの役割:
1. Hugging Face から best.pt をダウンロードする
2. Djangoプロジェクト内の prediction/models/ にコピーする
3. ファイル名を public_fire_smoke_yolov8n_best.pt に統一する

注意:
- APIキーやパスワードは使いません。
- 既存の自作Gion YOLOモデルは上書きしません。
"""

from pathlib import Path
from shutil import copyfile

from huggingface_hub import hf_hub_download


def main():
    """
    ダウンロード処理の本体です。
    """

    # このファイルが置かれている場所を基準にします。
    # manage.py と同じ場所に置く前提です。
    base_dir = Path(__file__).resolve().parent

    # Djangoアプリ内のモデル保存先です。
    model_dir = base_dir / "prediction" / "models"
    model_dir.mkdir(parents=True, exist_ok=True)

    # 最終的に保存するファイル名です。
    # 既存のGion YOLOモデルと混ざらないように、public_ を付けています。
    save_path = model_dir / "public_fire_smoke_yolov8n_best.pt"

    print("公開YOLOモデルをダウンロードしています...")

    # Hugging Faceから best.pt を取得します。
    downloaded_path = hf_hub_download(
        repo_id="rabahdev/fire-smoke-yolov8n",
        filename="best.pt",
    )

    # ダウンロードしたファイルを、Djangoプロジェクト内にコピーします。
    copyfile(downloaded_path, save_path)

    print("ダウンロード完了")
    print(f"保存先: {save_path}")

    if save_path.exists():
        print("確認OK: モデルファイルが存在します。")
    else:
        print("確認NG: モデルファイルが見つかりません。")


if __name__ == "__main__":
    main()