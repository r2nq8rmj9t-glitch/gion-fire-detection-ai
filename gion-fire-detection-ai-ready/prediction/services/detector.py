from pathlib import Path

from django.conf import settings


"""
detector.py

このファイルの役割:
- YOLOv8モデルを読み込む
- 画像から fire / smoke を物体検出する
- 検出枠付き画像を保存する
- 検出結果を fusion.py や home.html で使いやすい形に整える

今回使うYOLOモデル:
1. Gion YOLO
   - 自作モデル
   - 祇園町向けの fire / smoke 検出

2. Public Fire-Smoke YOLO
   - 公開モデル
   - smoke / fire の補助検出
"""


# AIモデルは読み込みに時間がかかります。
# 毎回読み込むと遅いため、一度読み込んだモデルを使い回します。
_gion_yolo_model = None
_public_yolo_model = None


# 自作Gion YOLOのクラス順です。
# 現在のモデルでは 0=smoke, 1=fire の前提です。
GION_YOLO_CLASS_NAMES = {
    0: "smoke",
    1: "fire",
}


# 公開Fire-Smoke YOLOのクラス順です。
# 今回使う公開モデルも 0=smoke, 1=fire の前提です。
PUBLIC_YOLO_CLASS_NAMES = {
    0: "smoke",
    1: "fire",
}


def get_gion_yolo_model():
    """
    自作Gion YOLOモデルを読み込む関数です。

    役割:
    - settings.py の YOLO_MODEL_PATH から .pt モデルを読み込む
    - 2回目以降は読み込み済みモデルを再利用する
    """

    global _gion_yolo_model

    if _gion_yolo_model is None:
        if not settings.YOLO_MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Gion YOLOモデルが見つかりません: {settings.YOLO_MODEL_PATH}"
            )

        from ultralytics import YOLO

        _gion_yolo_model = YOLO(str(settings.YOLO_MODEL_PATH))

    return _gion_yolo_model


def get_public_yolo_model():
    """
    公開Fire-Smoke YOLOモデルを読み込む関数です。

    役割:
    - settings.py の PUBLIC_FIRE_SMOKE_YOLO_MODEL_PATH から .pt モデルを読み込む
    - smoke / fire の補助検出に使う
    """

    global _public_yolo_model

    if _public_yolo_model is None:
        if not settings.PUBLIC_FIRE_SMOKE_YOLO_MODEL_PATH.exists():
            raise FileNotFoundError(
                f"公開Fire-Smoke YOLOモデルが見つかりません: "
                f"{settings.PUBLIC_FIRE_SMOKE_YOLO_MODEL_PATH}"
            )

        from ultralytics import YOLO

        _public_yolo_model = YOLO(str(settings.PUBLIC_FIRE_SMOKE_YOLO_MODEL_PATH))

    return _public_yolo_model


def build_detection_items(boxes, class_names):
    """
    YOLOの検出結果を、画面表示しやすい形に変換する関数です。

    YOLOのboxesには、検出された枠の情報が入っています。

    返す情報:
    - label: fire / smoke
    - confidence: 0〜1 の信頼度
    - confidence_percent: 画面表示用の %
    - xyxy: 検出枠の座標
    - area: 検出枠の面積

    areaを使う理由:
    - 小さい赤い光だけを fire と拾っているのか
    - 大きな煙全体を smoke と拾っているのか
    を後で分析しやすくするためです。
    """

    detection_items = []

    if boxes is None or len(boxes) == 0:
        return detection_items

    for box in boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        label = class_names.get(class_id, "unknown")

        # xyxy は [左上x, 左上y, 右下x, 右下y] です。
        xyxy = [round(float(value), 1) for value in box.xyxy[0].tolist()]
        x1, y1, x2, y2 = xyxy

        width = max(x2 - x1, 0)
        height = max(y2 - y1, 0)
        area = round(width * height, 1)

        detection_items.append(
            {
                "label": label,
                "class_id": class_id,
                "confidence": round(confidence, 3),
                "confidence_percent": round(confidence * 100, 1),
                "xyxy": xyxy,
                "area": area,
            }
        )

    return detection_items


def save_annotated_image(yolo_result, image_path, suffix):
    """
    YOLOの検出枠付き画像を保存する関数です。

    役割:
    - YOLOが検出した fire / smoke の枠を画像に描画する
    - media/results/ に保存する
    - ブラウザ表示用URLを返す

    suffix:
    - gion_yolo
    - public_yolo

    このsuffixを付けることで、2つのYOLO結果画像が上書きされないようにします。
    """

    result_dir = settings.MEDIA_ROOT / "results"
    result_dir.mkdir(parents=True, exist_ok=True)

    image_path = Path(image_path)

    annotated_name = f"{image_path.stem}_{suffix}.jpg"
    annotated_path = result_dir / annotated_name

    # yolo_result.save() により、検出枠付き画像が保存されます。
    # 検出がない場合は、枠なし画像として保存されます。
    yolo_result.save(filename=str(annotated_path))

    annotated_image_url = settings.MEDIA_URL + "results/" + annotated_name

    return annotated_image_url


def run_yolo_detection(
    image_path,
    model,
    class_names,
    model_name,
    annotated_suffix,
    conf=0.25,
):
    """
    YOLO推論の共通処理です。

    役割:
    - Gion YOLO と Public YOLO の両方で使えるようにする
    - 推論処理、検出結果整理、検出枠付き画像保存をまとめる

    戻り値:
    {
        "mode": "detection",
        "model_name": "gion_yolo",
        "result_label": "fire" / "smoke" / "no_detection",
        "confidence": 0.0〜1.0,
        "confidence_percent": 0.0〜100.0,
        "annotated_image_url": "...",
        "detections": [...]
    }
    """

    results = model.predict(
        source=str(image_path),
        conf=conf,
        save=False,
        verbose=False,
    )

    yolo_result = results[0]

    annotated_image_url = save_annotated_image(
        yolo_result=yolo_result,
        image_path=image_path,
        suffix=annotated_suffix,
    )

    boxes = yolo_result.boxes

    detection_items = build_detection_items(
        boxes=boxes,
        class_names=class_names,
    )

    if not detection_items:
        return {
            "mode": "detection",
            "model_name": model_name,
            "result_label": "no_detection",
            "confidence": 0,
            "confidence_percent": 0.0,
            "annotated_image_url": annotated_image_url,
            "detections": [],
        }

    # 代表結果は、confidenceが一番高い検出候補にします。
    best_detection = max(
        detection_items,
        key=lambda item: item["confidence"],
    )

    return {
        "mode": "detection",
        "model_name": model_name,
        "result_label": best_detection["label"],
        "confidence": best_detection["confidence"],
        "confidence_percent": best_detection["confidence_percent"],
        "annotated_image_url": annotated_image_url,
        "detections": detection_items,
    }


def run_detection(image_path):
    """
    自作Gion YOLOで fire / smoke を検出する関数です。

    役割:
    - これまで使っていたメインのYOLO検出
    - 祇園町向けの fire / smoke 判定
    """

    model = get_gion_yolo_model()

    return run_yolo_detection(
        image_path=image_path,
        model=model,
        class_names=GION_YOLO_CLASS_NAMES,
        model_name="gion_yolo",
        annotated_suffix="gion_yolo",
        conf=0.25,
    )


def run_public_fire_smoke_detection(image_path):
    """
    公開Fire-Smoke YOLOで smoke / fire を検出する関数です。

    役割:
    - 追加した公開モデルを使う
    - smoke判定の補助材料にする
    - Gion YOLOの結果と比較する
    """

    model = get_public_yolo_model()

    return run_yolo_detection(
        image_path=image_path,
        model=model,
        class_names=PUBLIC_YOLO_CLASS_NAMES,
        model_name="public_fire_smoke_yolo",
        annotated_suffix="public_yolo",
        conf=0.25,
    )