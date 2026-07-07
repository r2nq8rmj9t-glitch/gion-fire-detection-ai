import numpy as np
from django.conf import settings
from PIL import Image


"""
prediction/services/classifier.py（TFLite版）

このファイルの役割:
- 画像全体を fire / normal / smoke に分類する
- 以前は TensorFlow/Keras を使っていたが、本番サーバー（メモリ512MB）で
  メモリ不足になるため、軽量な TFLite ランタイムに置き換えた
- 変換済みモデル（gion_fire_MNV2.tflite）は元のKerasモデルと
  出力が一致することを検証済み（最大誤差 約0.000001）
"""


_interpreter = None


def _import_interpreter_class():
    """
    TFLiteの実行エンジン（Interpreter）を読み込む。

    環境によって入っているパッケージ名が違うため、順に試す:
      1. ai_edge_litert（新しい公式軽量パッケージ・本番用）
      2. tflite_runtime（旧パッケージ。2023年で更新停止のため、
         新しい形式のモデルを読めないことがある。保険としてのみ)
      3. tensorflow.lite（開発PCにTensorFlowがある場合の保険）
    """
    try:
        from ai_edge_litert.interpreter import Interpreter
        return Interpreter
    except ImportError:
        pass

    try:
        from tflite_runtime.interpreter import Interpreter
        return Interpreter
    except ImportError:
        pass

    from tensorflow.lite import Interpreter
    return Interpreter


def _get_tflite_model_path():
    """
    TFLiteモデルファイルの場所を返す。
    settings.py に CLASSIFICATION_TFLITE_PATH があればそれを使い、
    無ければ AI_MODEL_DIR / "gion_fire_MNV2.tflite" を使う。
    """
    return getattr(
        settings,
        "CLASSIFICATION_TFLITE_PATH",
        settings.AI_MODEL_DIR / "gion_fire_MNV2.tflite",
    )


def get_classification_model():
    """
    TFLiteのInterpreter（分類モデル本体）を読み込む。
    必要になった時だけ読み込むことで、YOLOモードの邪魔をしない。
    """
    global _interpreter

    if _interpreter is None:
        model_path = _get_tflite_model_path()

        if not model_path.exists():
            raise FileNotFoundError(
                f"分類モデル(TFLite)が見つかりません: {model_path}"
            )

        Interpreter = _import_interpreter_class()

        # num_threads=1: メモリとCPUの使用を最小限に抑える
        _interpreter = Interpreter(model_path=str(model_path), num_threads=1)
        _interpreter.allocate_tensors()

    return _interpreter


def run_classification(image_path):
    """
    画像全体を fire / normal / smoke に分類する。
    戻り値の形式は旧Keras版と完全に同じ。
    """
    interpreter = get_classification_model()

    pil_img = Image.open(image_path)

    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")

    pil_img = pil_img.resize((224, 224))

    # MobileNetV2のpreprocess_input相当: 画素値を -1〜+1 に変換
    img_array = np.asarray(pil_img, dtype=np.float32)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 127.5 - 1.0

    input_detail = interpreter.get_input_details()[0]
    output_detail = interpreter.get_output_details()[0]

    interpreter.set_tensor(input_detail["index"], img_array)
    interpreter.invoke()
    result = interpreter.get_tensor(output_detail["index"])

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
