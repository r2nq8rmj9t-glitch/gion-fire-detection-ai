import json
from datetime import datetime
from shutil import copyfile
from uuid import uuid4

from django.conf import settings


"""
feedback.py

このファイルの役割:
- ユーザーが押した「正解 / 誤検知 / 見逃し」のフィードバックを保存する
- アップロード画像を media/feedback/ にコピーする
- AIの判定結果を JSON として保存する
- 保存済みフィードバックを一覧画面に渡せる形で読み込む

セキュリティ上の注意:
- MEDIA_ROOT の外にあるファイルは扱わない
- 外部入力をそのままファイル実行しない
- JSONは表示用データとして読むだけにする
"""


FEEDBACK_CATEGORY_DIRS = {
    "correct": "correct",
    "false_positive_red_lantern": "false_positive_red_lantern",
    "false_positive_non_fire_smoke": "false_positive_non_fire_smoke",
    "missed_fire_or_smoke": "missed_fire_or_smoke",
    "other": "other",
}


FEEDBACK_CATEGORY_LABELS = {
    "correct": "正しく判定",
    "false_positive_red_lantern": "誤検知：赤い提灯・赤色照明",
    "false_positive_non_fire_smoke": "誤検知：料理煙・湯気",
    "missed_fire_or_smoke": "見逃し：火・煙がある",
    "other": "その他",
}


def media_url_to_path(image_url):
    """
    ブラウザ表示用の画像URLを、PC内のファイルパスに変換します。

    例:
    /media/uploads/sample.jpg
    ↓
    C:/.../media/uploads/sample.jpg
    """

    if not image_url:
        raise ValueError("画像URLが空です。")

    media_url = settings.MEDIA_URL

    if not image_url.startswith(media_url):
        raise ValueError("media配下の画像ではありません。")

    relative_path = image_url.replace(media_url, "", 1)

    file_path = (settings.MEDIA_ROOT / relative_path).resolve()
    media_root = settings.MEDIA_ROOT.resolve()

    if media_root not in file_path.parents and file_path != media_root:
        raise ValueError("不正な画像パスです。")

    if not file_path.exists():
        raise FileNotFoundError(f"画像ファイルが見つかりません: {file_path}")

    return file_path


def save_feedback_log(
    image_url,
    category,
    selected_mode,
    final_title,
    final_summary,
    final_level,
    note="",
):
    """
    誤検知・正解フィードバックを保存する関数です。

    保存するもの:
    1. 判定に使った画像のコピー
    2. 判定結果やメモを入れた JSON ファイル
    """

    category_dir_name = FEEDBACK_CATEGORY_DIRS.get(category, "other")

    source_image_path = media_url_to_path(image_url)

    feedback_dir = settings.MEDIA_ROOT / "feedback" / category_dir_name
    feedback_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid4().hex[:8]
    suffix = source_image_path.suffix.lower()

    base_name = f"{timestamp}_{unique_id}"

    saved_image_path = feedback_dir / f"{base_name}{suffix}"
    saved_json_path = feedback_dir / f"{base_name}.json"

    copyfile(source_image_path, saved_image_path)

    metadata = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "category": category,
        "category_dir": category_dir_name,
        "category_label": FEEDBACK_CATEGORY_LABELS.get(category, "その他"),
        "selected_mode": selected_mode,
        "final_title": final_title,
        "final_summary": final_summary,
        "final_level": final_level,
        "note": note,
        "source_image_url": image_url,
        "saved_image": str(saved_image_path),
    }

    with open(saved_json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return {
        "saved_image_path": saved_image_path,
        "saved_json_path": saved_json_path,
    }


def find_feedback_image(json_path):
    """
    JSONファイルと同じ名前の画像ファイルを探します。

    例:
    20260701_143403_6353051d.json
    ↓
    20260701_143403_6353051d.jpg
    """

    image_suffixes = [".jpg", ".jpeg", ".png", ".webp"]

    for suffix in image_suffixes:
        image_path = json_path.with_suffix(suffix)

        if image_path.exists():
            return image_path

    return None


def image_path_to_media_url(image_path):
    """
    PC内の画像パスを、ブラウザ表示用URLに変換します。

    例:
    C:/.../media/feedback/correct/sample.jpg
    ↓
    /media/feedback/correct/sample.jpg
    """

    if not image_path:
        return ""

    media_root = settings.MEDIA_ROOT.resolve()
    resolved_image_path = image_path.resolve()

    if media_root not in resolved_image_path.parents and resolved_image_path != media_root:
        return ""

    relative_path = resolved_image_path.relative_to(media_root).as_posix()

    return settings.MEDIA_URL + relative_path


def list_feedback_logs(category="all"):
    """
    保存済みフィードバックを一覧表示用に読み込みます。

    category:
    - all
    - correct
    - false_positive_red_lantern
    - false_positive_non_fire_smoke
    - missed_fire_or_smoke
    - other
    """

    feedback_root = settings.MEDIA_ROOT / "feedback"
    feedback_root.mkdir(parents=True, exist_ok=True)

    valid_categories = set(FEEDBACK_CATEGORY_DIRS.keys())

    if category not in valid_categories:
        category = "all"

    logs = []
    category_counts = {
        key: 0
        for key in FEEDBACK_CATEGORY_DIRS.keys()
    }

    for category_key, category_dir_name in FEEDBACK_CATEGORY_DIRS.items():
        category_dir = feedback_root / category_dir_name

        if not category_dir.exists():
            continue

        if category != "all" and category != category_key:
            continue

        json_files = sorted(
            category_dir.glob("*.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

        for json_path in json_files:
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                image_path = find_feedback_image(json_path)
                saved_image_url = image_path_to_media_url(image_path)

                category_from_json = data.get("category", category_key)

                if category_from_json in category_counts:
                    category_counts[category_from_json] += 1

                logs.append(
                    {
                        "created_at": data.get("created_at", ""),
                        "category": category_from_json,
                        "category_label": FEEDBACK_CATEGORY_LABELS.get(
                            category_from_json,
                            "その他",
                        ),
                        "selected_mode": data.get("selected_mode", ""),
                        "final_title": data.get("final_title", ""),
                        "final_summary": data.get("final_summary", ""),
                        "final_level": data.get("final_level", ""),
                        "note": data.get("note", ""),
                        "source_image_url": data.get("source_image_url", ""),
                        "saved_image_url": saved_image_url,
                        "json_filename": json_path.name,
                    }
                )

            except Exception:
                # 壊れたJSONがあっても一覧画面全体を止めないため、スキップします。
                continue

    logs = sorted(
        logs,
        key=lambda item: item.get("created_at", ""),
        reverse=True,
    )

    all_count = sum(category_counts.values())

    return {
        "logs": logs,
        "category_counts": category_counts,
        "all_count": all_count,
        "selected_category": category,
    }