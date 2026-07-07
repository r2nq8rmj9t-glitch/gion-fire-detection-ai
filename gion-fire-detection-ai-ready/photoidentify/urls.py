from django.conf import settings
from django.contrib import admin
from django.urls import path, re_path
from django.views.static import serve

from prediction import views


"""
photoidentify/urls.py

このファイルの役割:
- ブラウザでアクセスしたURLを、どの処理に渡すか決める
- トップページは predict
- フィードバック保存は save_feedback
- フィードバック一覧は feedback_list
- media ファイル（アップロード画像・判定結果画像）を配信する
"""


urlpatterns = [
    # Django管理画面
    path("admin/", admin.site.urls),

    # トップページ
    path("", views.predict, name="predict"),

    # 判定フィードバック保存
    path("feedback/", views.save_feedback, name="save_feedback"),

    # フィードバック一覧画面
    path("feedback-list/", views.feedback_list, name="feedback_list"),
]


# アップロード画像と判定結果画像を配信します。
#
# 重要な注意:
# django.conf.urls.static.static() は DEBUG=False のとき
# 何も返さない仕様のため、本番では使えません。
# そのため serve() を直接登録しています。
#
# 本来、本番では S3 などの外部ストレージを使うべきですが、
# 今回はポートフォリオ確認用デモのための簡易対応です。
urlpatterns += [
    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]
