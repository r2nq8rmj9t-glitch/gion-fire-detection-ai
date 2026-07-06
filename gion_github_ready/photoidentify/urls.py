from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from prediction import views


"""
photoidentify/urls.py

このファイルの役割:
- ブラウザでアクセスしたURLを、どの処理に渡すか決める
- トップページは predict
- フィードバック保存は save_feedback
- フィードバック一覧は feedback_list
- 開発中だけ media ファイルを表示できるようにする
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


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )