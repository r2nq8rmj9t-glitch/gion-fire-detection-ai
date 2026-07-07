from django import forms


class ImageUploadForm(forms.Form):
    """
    画像アップロード画面で使うフォームです。

    このフォームの役割:
    1. ユーザーから画像ファイルを受け取る
    2. ユーザーに判定モードを選んでもらう
    3. views.py に「画像」と「判定モード」を渡す

    判定モード:
    - fusion: 3モデル統合判定
    - detection: Gion YOLOだけの物体検出
    - classification: MobileNetV2系モデルだけの画像分類
    """

    MODE_CHOICES = [
        ("fusion", "統合判定モード"),
        ("detection", "物体検出モード"),
        ("classification", "画像分類モード"),
    ]

    image = forms.ImageField(
        label="画像を選択"
    )

    mode = forms.ChoiceField(
        label="判定モード",
        choices=MODE_CHOICES,
        widget=forms.RadioSelect,
        initial="fusion",
    )