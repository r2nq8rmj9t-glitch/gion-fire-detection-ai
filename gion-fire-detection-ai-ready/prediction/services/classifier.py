import numpy as np
from django.conf import settings
from PIL import Image


_classification_model = None


def get_classification_model():
    """
    MobileNetV2系の画像分類モデルを読み込む。
    必要になった時だけ読み込むことで、YOLOモードの邪魔をしない。
    """
    global _classification_model

    if _classification_model is None:
        if not settings.CLASSIFICATION_MODEL_PATH.exists():
            raise FileNotFoundError(
                f"分類モデルが見つかりません: {settings.CLASSIFICATION_MODEL_PATH}"
            )

        from tensorflow.keras.models import load_model

        _classification_model = load_model(str(settings.CLASSIFICATION_MODEL_PATH))

    return _classification_model


def run_classification(image_path):
    """
    画像全体を fire / normal / smoke に分類する。
    """
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
    from tensorflow.keras.preprocessing.image import img_to_array

    model = get_classification_model()

    pil_img = Image.open(image_path)

    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")

    pil_img = pil_img.resize((224, 224))

    img_array = img_to_array(pil_img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)

    result = model.predict(img_array, verbose=0)

    output_count = result.shape[-1]

    if output_count != len(settings.CLASSIFICATION_CLASS_NAMES):
        raise ValueError(
            f"分類モデルの出力数が想定外です。"
            f"出力数: {output_count}, "
            f"クラス名数: {len(settings.CLASSIFICATION_CLASS_NAMES)}"
        )

    probs = result[0]
    sorted_indexes = np.argsort(probs)[::-1]

    predictions = [
        {
            "rank": i + 1,
            "label": settings.CLASSIFICATION_CLASS_NAMES[index],
            "prob": round(float(probs[index]) * 100, 2),
        }
        for i, index in enumerate(sorted_indexes)
    ]

    return {
        "mode": "classification",
        "predictions": predictions,
    }