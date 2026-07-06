# 祇園町火災検知AI Djangoアプリ

京都・祇園町南側の街並みを想定した、火災・煙検知AIのポートフォリオ作品です。  
画像をアップロードすると、YOLOv8による物体検出とMobileNetV2系の画像分類を組み合わせて、火災・煙・通常・赤色照明反応などを判定します。

## 制作目的

祇園町南側は、木造建築、飲食店、赤い提灯、暖色照明、料理煙などが多い地域です。  
一般的な火災検知AIでは、赤い照明や湯気を火災として誤検知する可能性があります。

このアプリでは、単に「火かどうか」を判定するのではなく、地域特性を考慮した誤検知対策と、再学習につなげるフィードバック保存機能を実装しました。

## 主な機能

- 画像アップロード判定
- ドラッグ＆ドロップによる画像選択
- アップロード画像のプレビュー表示
- 自作Gion YOLOモデルによる fire / smoke 物体検出
- 公開Fire-Smoke YOLOモデルによる補助検出
- MobileNetV2系画像分類モデルによる fire / normal / smoke 分類
- 3モデル統合判定
- 赤い提灯・赤色照明への誤検知対策
- YOLO検出枠付き画像の表示
- 判定理由の表示
- 判定フィードバック保存
- フィードバック履歴一覧画面
- カテゴリ別フィルター表示

## 判定モード

| モード | 内容 |
|---|---|
| 統合判定モード | Gion YOLO、公開Fire-Smoke YOLO、画像分類AIを組み合わせて判定 |
| 物体検出モード | 自作Gion YOLOだけで fire / smoke の位置を検出 |
| 画像分類モード | MobileNetV2系モデルで画像全体を fire / normal / smoke に分類 |

## 使用モデル

| モデル | ファイル | 役割 |
|---|---|---|
| 画像分類モデル | `prediction/models/260627model_gion_fire_MNV2.h5.keras` | 画像全体を fire / normal / smoke に分類 |
| 自作Gion YOLO | `prediction/models/gion_fire_yolov8n_finetune_v2_best.pt` | 祇園町向けの火・煙の位置検出 |
| 公開Fire-Smoke YOLO | `prediction/models/public_fire_smoke_yolov8n_best.pt` | 火・煙検出の補助 |

Gion YOLOのクラス順は以下です。

```txt
0 = smoke
1 = fire
```

## 統合判定ロジック

このアプリでは、1つのAIモデルだけで最終判定を決めません。  
祇園町で誤検知になりやすい赤い提灯、暖色照明、料理煙、湯気などを考慮するため、複数モデルの結果を統合しています。

特に以下の条件では、火災確定ではなく「赤色照明反応」として扱います。

```txt
画像分類AI = fire
Gion YOLO = fire / smoke 検出なし
公開Fire-Smoke YOLO = fire / smoke 検出なし
```

この条件では、画像全体の赤色に分類AIが反応した可能性があるため、火災リスクを強く扱いすぎないようにしています。

## フィードバック保存機能

AI判定後、判定結果に対してフィードバックを保存できます。

| カテゴリ | 意味 |
|---|---|
| correct | AI判定が正しかった画像 |
| false_positive_red_lantern | 赤い提灯・赤色照明の誤検知 |
| false_positive_non_fire_smoke | 料理煙・湯気の誤検知 |
| missed_fire_or_smoke | 火・煙の見逃し |
| other | その他の改善用データ |

保存された画像とJSONは、再学習用データの整理に使う想定です。

## フィードバック履歴画面

```txt
http://127.0.0.1:8000/feedback-list/
```

一覧画面では、保存画像、カテゴリ、判定モード、判定タイトル、最終判定、リスクレベル、メモ、JSONファイル名を確認できます。

## 技術構成

| 分野 | 使用技術 |
|---|---|
| Webアプリ | Django |
| 画像処理 | Pillow |
| 物体検出 | YOLOv8 / Ultralytics |
| 画像分類 | TensorFlow / Keras / MobileNetV2系モデル |
| 言語 | Python |
| 保存 | ローカルファイル / JSON |
| 画面 | HTML / CSS / Bootstrap |

## ディレクトリ構成

```txt
photoidentify/
├── manage.py
├── README.md
├── requirements.txt
├── photoidentify/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── prediction/
│   ├── forms.py
│   ├── views.py
│   ├── models.py
│   ├── services/
│   │   ├── classifier.py
│   │   ├── detector.py
│   │   ├── fusion.py
│   │   └── feedback.py
│   ├── models/
│   │   ├── 260627model_gion_fire_MNV2.h5.keras
│   │   ├── gion_fire_yolov8n_finetune_v2_best.pt
│   │   └── public_fire_smoke_yolov8n_best.pt
│   └── templates/
│       ├── home.html
│       └── feedback_list.html
└── media/
    ├── uploads/
    ├── results/
    └── feedback/
```

## セットアップ方法

```bash
cd photoidentify
python -m venv .venv
.venv\Scriptsctivate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py runserver
```

起動後、ブラウザで以下を開きます。

```txt
http://127.0.0.1:8000/
```

## 使い方

1. トップ画面を開く
2. 画像をドラッグ＆ドロップ、またはクリックして選択する
3. 判定モードを選ぶ
4. 「AIで判定する」を押す
5. 判定結果、判定理由、検出枠付き画像を確認する
6. 必要に応じてフィードバックを保存する
7. フィードバック履歴画面で保存結果を確認する

## 工夫した点

### 地域特性を考慮した設計

祇園町南側の木造町家、赤い提灯、暖色照明、料理煙、湯気などを考慮し、単純な火災判定ではなく、誤検知を抑える統合判定を設計しました。

### 複数モデルの統合

YOLOv8による位置検出と、MobileNetV2系画像分類モデルを組み合わせることで、画像全体の雰囲気だけに依存しない判定を目指しました。

### フィードバックによる改善サイクル

誤検知や見逃しを保存し、再学習データとして活用できるようにしました。AIモデルを一度作って終わりにせず、運用しながら改善する設計にしています。

### 判定理由の表示

最終判定だけでなく、各モデルの判定結果や信頼度、検出有無を表示し、なぜその結果になったのかを確認できるようにしました。

## 現在の課題

| 課題 | 内容 |
|---|---|
| モデル精度 | 赤い提灯や暖色照明への誤判定は完全には解消していない |
| データ数 | 祇園町特化の実画像データはまだ十分ではない |
| 保存方式 | フィードバック履歴はDBではなくファイル保存 |
| UI | 今後、Liquid Glass風UIや祇園町マップ表示に改善予定 |
| 実運用 | 現在は画像アップロード判定であり、リアルタイム監視ではない |

## 今後の改善予定

- Liquid Glass UIへの改良
- 祇園町マップ表示
- マップ上への判定ピン表示
- フィードバックデータの削除・編集機能
- 再学習用データのエクスポート機能
- リアルタイム監視カメラ連携の検討

## 注意事項

このアプリは就職活動用ポートフォリオとして制作した検証用アプリです。  
実際の火災判断や防災設備として使用するものではありません。

公開モデルを利用する場合は、配布元のライセンス・利用条件を確認してください。

## 制作者

大仲 謙志

Python / Django / YOLOv8 / TensorFlow を用いて、京都・祇園町向けの火災検知AIアプリを制作しました。
