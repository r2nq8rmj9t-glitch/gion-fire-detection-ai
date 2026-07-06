from uuid import uuid4

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import ImageUploadForm
from .services.classifier import run_classification
from .services.detector import (
    run_detection,
    run_public_fire_smoke_detection,
)

from .services.feedback import (
    FEEDBACK_CATEGORY_LABELS,
    list_feedback_logs,
    save_feedback_log,
)
from .services.fusion import run_fusion


def save_uploaded_image(image_file):
    """
    アップロードされた画像を media/uploads/ に保存する関数です。

    なぜ保存するのか:
    1. YOLOv8は画像ファイルのパスを使って推論するため
    2. アップロード画像を画面に再表示するため
    3. 同じ名前の画像で上書きされないようにするため

    戻り値:
    - image_path: AI推論に使うPC内の保存パス
    - image_url: ブラウザ表示に使うURL
    """

    upload_dir = settings.MEDIA_ROOT / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    original_name = image_file.name
    suffix = original_name.split(".")[-1].lower()

    saved_name = f"{uuid4().hex}.{suffix}"
    image_path = upload_dir / saved_name

    with open(image_path, "wb+") as destination:
        for chunk in image_file.chunks():
            destination.write(chunk)

    image_url = settings.MEDIA_URL + "uploads/" + saved_name

    return image_path, image_url


def predict(request):
    """
    画像判定ページのメイン処理です。

    この関数の役割:
    1. 画像アップロードフォームを表示する
    2. POSTされた画像を受け取る
    3. 選択された判定モードを確認する
    4. モードに応じてAIモデルを呼び出す
    5. 判定結果を home.html に渡す

    判定モード:
    - fusion: Gion YOLO + Public YOLO + MobileNetV2 の統合判定
    - detection: Gion YOLOだけの物体検出
    - classification: MobileNetV2系モデルだけの画像分類
    """

    form = ImageUploadForm()

    context = {
        "form": form,
        "selected_mode": None,
        "uploaded_image_url": None,

        # 統合判定結果
        "fusion_result": None,

        # Gion YOLO結果
        "detection_result_label": None,
        "detection_confidence": None,
        "detection_items": None,
        "annotated_image_url": None,

        # Public YOLO結果
        "public_detection_result_label": None,
        "public_detection_confidence": None,
        "public_detection_items": None,
        "public_annotated_image_url": None,

        # 画像分類結果
        "classification_predictions": None,

        # エラー表示
        "error_message": None,
    }

    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)
        context["form"] = form

        if form.is_valid():
            image_file = form.cleaned_data["image"]
            selected_mode = form.cleaned_data["mode"]
            context["selected_mode"] = selected_mode

            try:
                image_path, image_url = save_uploaded_image(image_file)
                context["uploaded_image_url"] = image_url

                # --------------------------------------------------
                # 統合判定モード
                # 3モデルをすべて実行します。
                # --------------------------------------------------
                if selected_mode == "fusion":
                    gion_detection_result = run_detection(image_path)
                    public_detection_result = run_public_fire_smoke_detection(image_path)
                    classification_result = run_classification(image_path)

                    fusion_result = run_fusion(
                        detection_result=gion_detection_result,
                        public_detection_result=public_detection_result,
                        classification_result=classification_result,
                    )

                    context["fusion_result"] = fusion_result

                    # Gion YOLO結果
                    context["detection_result_label"] = gion_detection_result["result_label"]
                    context["detection_confidence"] = gion_detection_result["confidence"]
                    context["detection_items"] = gion_detection_result["detections"]
                    context["annotated_image_url"] = gion_detection_result["annotated_image_url"]

                    # Public YOLO結果
                    context["public_detection_result_label"] = public_detection_result["result_label"]
                    context["public_detection_confidence"] = public_detection_result["confidence"]
                    context["public_detection_items"] = public_detection_result["detections"]
                    context["public_annotated_image_url"] = public_detection_result["annotated_image_url"]

                    # 画像分類結果
                    context["classification_predictions"] = classification_result["predictions"]

                # --------------------------------------------------
                # 物体検出モード
                # Gion YOLOだけを実行します。
                # --------------------------------------------------
                elif selected_mode == "detection":
                    gion_detection_result = run_detection(image_path)

                    context["detection_result_label"] = gion_detection_result["result_label"]
                    context["detection_confidence"] = gion_detection_result["confidence"]
                    context["detection_items"] = gion_detection_result["detections"]
                    context["annotated_image_url"] = gion_detection_result["annotated_image_url"]

                # --------------------------------------------------
                # 画像分類モード
                # MobileNetV2系モデルだけを実行します。
                # --------------------------------------------------
                elif selected_mode == "classification":
                    classification_result = run_classification(image_path)

                    context["classification_predictions"] = classification_result["predictions"]

                else:
                    context["error_message"] = "不明な判定モードです。"

            except FileNotFoundError as e:
                context["error_message"] = str(e)

            except Exception as e:
                context["error_message"] = f"判定中にエラーが発生しました: {e}"

        else:
            context["error_message"] = "画像と判定モードを選択してください。"

    return render(request, "home.html", context)


@require_POST
def save_feedback(request):
    """
    ユーザーのフィードバックを保存するビューです。

    役割:
    - home.html のフィードバックボタンからPOSTを受け取る
    - 画像と判定結果を media/feedback/ に保存する
    - 保存後、トップ画面へ戻す

    注意:
    - 画像そのものは再アップロードしません。
    - すでに media/uploads/ に保存された画像を feedback フォルダへコピーします。
    """

    image_url = request.POST.get("image_url", "")
    category = request.POST.get("category", "other")
    selected_mode = request.POST.get("selected_mode", "")
    final_title = request.POST.get("final_title", "")
    final_summary = request.POST.get("final_summary", "")
    final_level = request.POST.get("final_level", "")
    note = request.POST.get("note", "")

    try:
        save_feedback_log(
            image_url=image_url,
            category=category,
            selected_mode=selected_mode,
            final_title=final_title,
            final_summary=final_summary,
            final_level=final_level,
            note=note,
        )

        messages.success(
            request,
            "フィードバックを保存しました。次回の改善データとして使えます。",
        )

    except Exception as e:
        messages.error(
            request,
            f"フィードバック保存中にエラーが発生しました: {e}",
        )

    return redirect("predict")

def feedback_list(request):
    """
    フィードバック一覧画面を表示するビューです。

    役割:
    - media/feedback/ に保存されたJSONと画像を読み込む
    - カテゴリ別にフィルターできるようにする
    - feedback_list.html に一覧データを渡す
    """

    selected_category = request.GET.get("category", "all")

    feedback_data = list_feedback_logs(category=selected_category)

    category_options = [
        {
            "key": "all",
            "label": "すべて",
            "count": feedback_data["all_count"],
        }
    ]

    for key, label in FEEDBACK_CATEGORY_LABELS.items():
        category_options.append(
            {
                "key": key,
                "label": label,
                "count": feedback_data["category_counts"].get(key, 0),
            }
        )

    context = {
        "feedback_logs": feedback_data["logs"],
        "category_options": category_options,
        "selected_category": feedback_data["selected_category"],
        "total_count": feedback_data["all_count"],
    }

    return render(request, "feedback_list.html", context)