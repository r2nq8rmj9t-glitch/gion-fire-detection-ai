# 祇園町火災検知AI（Gion Fire Detection AI）

京都・祇園町南側の景観を想定した、火災・煙検知AIのポートフォリオアプリです。
画像をアップロードすると、YOLOv8による物体検出とMobileNetV2系画像分類モデルを
組み合わせて、火災リスクを判定します。

- GitHub: https://github.com/r2nq8rmj9t-glitch/gion-fire-detection-ai
- デモ動画: https://youtu.be/hQD0N5gubKA

## 注意事項

> **このアプリはポートフォリオ用の検証アプリです。**
> **実際の火災通報・防災判断には使用しないでください。**

- 本番公開版はポートフォリオ確認用のデモです。
- アップロード画像はRenderの再起動時に消えます（永続保存されません）。
- サーバーのメモリ制限により、AI推論を停止した軽量デモ版として
  公開している場合があります。その場合、AI推論の動作はデモ動画で確認できます。

## 判定モード

| モード | 内容 |
|---|---|
| 統合判定 | Gion YOLO + 公開Fire-Smoke YOLO + MobileNetV2 の3モデル統合判定 |
| 物体検出 | Gion YOLO（自作モデル）のみ |
| 画像分類 | MobileNetV2系モデルのみ（fire / normal / smoke） |

## ローカル起動

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

http://127.0.0.1:8000/ を開きます。
