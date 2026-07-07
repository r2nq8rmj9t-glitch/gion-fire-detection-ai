def get_top_classification_label(classification_result):
    """
    画像分類モデルの結果から、1位の判定だけを取り出す関数です。

    classification_result の想定:
    {
        "predictions": [
            {"rank": 1, "label": "smoke", "prob": 100.0},
            {"rank": 2, "label": "fire", "prob": 0.0},
            {"rank": 3, "label": "normal", "prob": 0.0},
        ]
    }

    戻り値:
    - top_label: 画像分類AIの1位ラベル
    - top_prob: 画像分類AIの1位確率
    """

    predictions = classification_result.get("predictions", [])

    # 分類結果が空でもアプリが落ちないようにする保険です。
    if not predictions:
        return "unknown", 0.0

    top_prediction = predictions[0]

    top_label = top_prediction.get("label", "unknown")
    top_prob = float(top_prediction.get("prob", 0.0))

    return top_label, top_prob


def label_to_japanese(label):
    """
    AI内部の英語ラベルを、日本語表示用に変換します。
    """

    label_map = {
        "fire": "火・炎",
        "smoke": "煙",
        "normal": "通常状態",
        "no_detection": "検出なし",
        "unknown": "不明",
    }

    return label_map.get(label, label)


def summarize_detection_result(detection_result):
    """
    YOLOの全検出結果を集計します。

    目的:
    - fire と smoke がそれぞれ何個出たかを見る
    - fire と smoke の最大信頼度を見る
    - fire と smoke の合計面積を見る
    - 小さな赤色だけを fire と拾っていないか判断しやすくする
    """

    detections = detection_result.get("detections", [])

    summary = {
        "fire_count": 0,
        "smoke_count": 0,
        "max_fire_confidence": 0.0,
        "max_smoke_confidence": 0.0,
        "max_fire_confidence_percent": 0.0,
        "max_smoke_confidence_percent": 0.0,
        "total_fire_area": 0.0,
        "total_smoke_area": 0.0,
    }

    for item in detections:
        label = item.get("label")
        confidence = float(item.get("confidence", 0.0))
        area = float(item.get("area", 0.0))

        if label == "fire":
            summary["fire_count"] += 1
            summary["total_fire_area"] += area

            if confidence > summary["max_fire_confidence"]:
                summary["max_fire_confidence"] = confidence

        elif label == "smoke":
            summary["smoke_count"] += 1
            summary["total_smoke_area"] += area

            if confidence > summary["max_smoke_confidence"]:
                summary["max_smoke_confidence"] = confidence

    summary["max_fire_confidence_percent"] = round(
        summary["max_fire_confidence"] * 100,
        1,
    )

    summary["max_smoke_confidence_percent"] = round(
        summary["max_smoke_confidence"] * 100,
        1,
    )

    summary["total_fire_area"] = round(summary["total_fire_area"], 1)
    summary["total_smoke_area"] = round(summary["total_smoke_area"], 1)

    return summary


def is_smoke_area_dominant(gion_summary, public_summary):
    """
    fire より smoke の面積がかなり大きいかを判定します。

    使う理由:
    - 煙が広く出ている
    - 一部に赤い部分がある
    - その赤い部分を fire と誤検知する

    このケースを「火災確定」ではなく、
    「煙優勢・要確認」に寄せるためです。
    """

    total_fire_area = (
        gion_summary["total_fire_area"]
        + public_summary["total_fire_area"]
    )

    total_smoke_area = (
        gion_summary["total_smoke_area"]
        + public_summary["total_smoke_area"]
    )

    if total_smoke_area <= 0:
        return False

    if total_fire_area <= 0:
        return True

    # smoke面積がfire面積の3倍以上なら煙優勢とします。
    # この3倍は暫定値です。テストしながら調整できます。
    return total_smoke_area >= total_fire_area * 3


def run_fusion(
    detection_result,
    classification_result,
    public_detection_result=None,
):
    """
    3モデルの結果を統合して、最終判定を作る関数です。

    使うモデル:
    1. Gion YOLO
       - 祇園向け fire / smoke 検出
       - fire判定の主役として扱います。

    2. Public Fire-Smoke YOLO
       - 公開モデル
       - smoke検出の補助として扱います。
       - fire判定は強く扱いすぎないようにします。

    3. MobileNetV2系 画像分類モデル
       - 画像全体を fire / normal / smoke に分類します。

    今回の重要改善:
    - 祇園町特有の赤い提灯・赤色照明を fire と誤判定しにくくします。
    - YOLOが火や煙の場所を検出していないのに、画像分類AIだけが fire と言った場合は、
      「赤い提灯・赤色照明の可能性」として扱います。
    """

    # 画像分類AIの1位結果を取り出します。
    classification_label, classification_probability = get_top_classification_label(
        classification_result
    )

    # Gion YOLOの代表結果と集計結果を取り出します。
    gion_label = detection_result.get("result_label", "unknown")
    gion_confidence_percent = detection_result.get("confidence_percent", 0.0)
    gion_summary = summarize_detection_result(detection_result)

    # Public YOLOの代表結果と集計結果を取り出します。
    if public_detection_result is None:
        public_detection_result = {
            "result_label": "no_detection",
            "confidence_percent": 0.0,
            "detections": [],
        }

    public_label = public_detection_result.get("result_label", "unknown")
    public_confidence_percent = public_detection_result.get("confidence_percent", 0.0)
    public_summary = summarize_detection_result(public_detection_result)

    # ------------------------------------------------------------
    # 各モデルの証拠を整理します。
    # ------------------------------------------------------------

    gion_fire_conf = gion_summary["max_fire_confidence"]
    gion_smoke_conf = gion_summary["max_smoke_confidence"]

    public_fire_conf = public_summary["max_fire_confidence"]
    public_smoke_conf = public_summary["max_smoke_confidence"]

    smoke_area_dominant = is_smoke_area_dominant(
        gion_summary=gion_summary,
        public_summary=public_summary,
    )

    # Gion YOLOのfireは主判断に使います。
    gion_strong_fire = gion_fire_conf >= 0.55

    # Public YOLOのfireは補助判断です。
    # 赤色・反射を拾う可能性があるため、しきい値を高めにしています。
    public_strong_fire = public_fire_conf >= 0.75

    # YOLO2種類がどちらも fire / smoke を検出していない状態です。
    both_yolo_no_detection = (
        gion_fire_conf == 0
        and gion_smoke_conf == 0
        and public_fire_conf == 0
        and public_smoke_conf == 0
    )

    # 今回の赤提灯対策の中心です。
    # 画像分類AIだけが fire と言っていて、
    # YOLO2種類がどちらも火・煙の場所を検出していない場合。
    classification_fire_only = (
        classification_label == "fire"
        and both_yolo_no_detection
    )

    # smoke は補助証拠として使います。
    smoke_evidence = (
        gion_smoke_conf >= 0.35
        or public_smoke_conf >= 0.35
        or classification_label == "smoke"
    )

    # fire 反応があるかどうかです。
    fire_evidence = (
        gion_fire_conf > 0
        or public_fire_conf > 0
        or classification_label == "fire"
    )

    # 公開YOLOだけが fire を出している状態です。
    public_fire_only = (
        public_fire_conf > 0
        and gion_fire_conf == 0
        and classification_label != "fire"
    )

    # 煙が広く、fire が小さく出ている状態です。
    smoke_dominant_with_fire_reaction = (
        smoke_area_dominant
        and fire_evidence
        and classification_label in ["smoke", "normal"]
    )

    # ------------------------------------------------------------
    # 総合判定ルール
    # ------------------------------------------------------------

    # 0. 赤い提灯・赤色照明対策
    # YOLOが何も検出していないのに、画像分類AIだけがfireと言う場合。
    if classification_fire_only:
        level = "caution"
        title = "赤い提灯・赤色照明の可能性があります"
        summary = "赤色照明反応"
        message = (
            "画像分類AIは画像全体を火・炎に近いと判断しましたが、"
            "Gion YOLOと公開Fire-Smoke YOLOは火や煙の場所を検出していません。"
            "祇園町では赤い提灯・赤い看板・暖色照明が多いため、"
            "火災ではなく赤色照明に反応している可能性があります。"
            "検出枠付き画像も確認してください。"
        )

    # 1. Gion YOLOが強くfireを出し、画像全体も危険寄りの場合
    elif gion_strong_fire and classification_label in ["fire", "smoke"]:
        level = "danger"
        title = "火災の可能性があります"
        summary = "火災リスクあり"
        message = (
            "自作Gion YOLOが火の候補を強く検出し、"
            "画像分類AIも火または煙の特徴を確認しました。"
            "火災リスクがある画像として、確認が必要です。"
        )

    # 2. Gion YOLOが強くfireを出しているが、分類AIはnormalの場合
    elif gion_strong_fire:
        level = "warning"
        title = "火のような反応があります"
        summary = "要確認"
        message = (
            "自作Gion YOLOが火の候補を強く検出しました。"
            "一方で、画像分類AIは画像全体を通常状態に近いと判断しています。"
            "赤い照明・反射・小さな炎色を拾っている可能性もあるため、"
            "検出枠付き画像を確認してください。"
        )

    # 3. 煙が広く、fire反応が一部にある場合
    elif smoke_dominant_with_fire_reaction:
        level = "caution"
        title = "煙の特徴が強く出ています"
        summary = "煙優勢・要確認"
        message = (
            "画像全体では煙の特徴が強く出ています。"
            "一部に火のような反応もありますが、"
            "赤い光・反射・小さな炎色を拾っている可能性があります。"
            "火災確定ではなく、煙優勢の要確認として扱います。"
        )

    # 4. 公開YOLOだけがfireを出している場合
    elif public_fire_only:
        level = "warning"
        title = "火のような反応があります"
        summary = "赤色反応・要確認"
        message = (
            "公開Fire-Smoke YOLOが火の候補を検出しました。"
            "ただし、自作Gion YOLOでは強いfire反応が確認されていません。"
            "赤い照明・反射・ランプ・小さな炎色を拾っている可能性があるため、"
            "要確認として扱います。"
        )

    # 5. Public YOLOのfireがかなり強く、smoke証拠もある場合
    elif public_strong_fire and smoke_evidence:
        level = "warning"
        title = "火または煙の反応があります"
        summary = "要確認"
        message = (
            "公開Fire-Smoke YOLOが強めの火の候補を検出し、"
            "煙の特徴も確認されています。"
            "ただし公開YOLOのfireは補助判定として扱うため、"
            "火災確定ではなく要確認とします。"
        )

    # 6. 煙の証拠がある場合
    elif smoke_evidence:
        level = "caution"
        title = "煙の特徴があります"
        summary = "煙の可能性あり"
        message = (
            "Gion YOLO、公開Fire-Smoke YOLO、または画像分類AIが煙の特徴を検出しました。"
            "火災煙の可能性もありますが、湯気・蒸気・料理煙・霧の可能性もあります。"
            "火災確定ではなく、注意判定として扱います。"
        )

    # 7. fire反応はあるが、強い根拠がない場合
    elif fire_evidence:
        level = "warning"
        title = "火のような反応があります"
        summary = "要確認"
        message = (
            "AIが火に近い特徴を検出しました。"
            "ただし、強い火災根拠までは確認できていません。"
            "赤い照明・反射・ランプなどを火と誤検知している可能性があります。"
        )

    # 8. どのモデルも火・煙を強く示していない場合
    else:
        level = "safe"
        title = "火や火災煙は検出されませんでした"
        summary = "火災リスク低"
        message = (
            "Gion YOLO、公開Fire-Smoke YOLO、画像分類AIのいずれも、"
            "火や火災煙を強く示していません。"
            "この画像では火災リスクは低いと考えられます。"
        )

    reason_lines = [
        f"Gion YOLOの代表判定: {label_to_japanese(gion_label)} / 信頼度: {gion_confidence_percent}%",
        f"Gion YOLOのfire最大信頼度: {gion_summary['max_fire_confidence_percent']}%",
        f"Gion YOLOのsmoke最大信頼度: {gion_summary['max_smoke_confidence_percent']}%",
        f"Gion YOLOのfire合計面積: {gion_summary['total_fire_area']}",
        f"Gion YOLOのsmoke合計面積: {gion_summary['total_smoke_area']}",
        f"公開Fire-Smoke YOLOの代表判定: {label_to_japanese(public_label)} / 信頼度: {public_confidence_percent}%",
        f"公開Fire-Smoke YOLOのfire最大信頼度: {public_summary['max_fire_confidence_percent']}%",
        f"公開Fire-Smoke YOLOのsmoke最大信頼度: {public_summary['max_smoke_confidence_percent']}%",
        f"公開Fire-Smoke YOLOのfire合計面積: {public_summary['total_fire_area']}",
        f"公開Fire-Smoke YOLOのsmoke合計面積: {public_summary['total_smoke_area']}",
        f"画像分類AIの判定: {label_to_japanese(classification_label)} / 確率: {classification_probability}%",
        f"YOLO未検出・分類AIのみfire判定: {'はい' if classification_fire_only else 'いいえ'}",
        f"煙優勢判定: {'はい' if smoke_area_dominant else 'いいえ'}",
        "赤い提灯・赤色照明が多い祇園町では、分類AIだけのfire判定を強く扱いすぎないようにしています。",
        "最終判定では、YOLOの位置検出、煙の面積、画像分類AIの結果を組み合わせています。",
    ]

    return {
        "level": level,
        "title": title,
        "message": message,
        "summary": summary,
        "reason_lines": reason_lines,

        # Gion YOLO
        "gion_label": gion_label,
        "gion_label_ja": label_to_japanese(gion_label),
        "gion_confidence_percent": gion_confidence_percent,
        "gion_summary": gion_summary,

        # Public YOLO
        "public_label": public_label,
        "public_label_ja": label_to_japanese(public_label),
        "public_confidence_percent": public_confidence_percent,
        "public_summary": public_summary,

        # Classification
        "classification_label": classification_label,
        "classification_label_ja": label_to_japanese(classification_label),
        "classification_probability": classification_probability,

        # 判定確認用
        "smoke_area_dominant": smoke_area_dominant,
        "gion_strong_fire": gion_strong_fire,
        "public_strong_fire": public_strong_fire,
        "public_fire_only": public_fire_only,
        "classification_fire_only": classification_fire_only,
        "both_yolo_no_detection": both_yolo_no_detection,
    }