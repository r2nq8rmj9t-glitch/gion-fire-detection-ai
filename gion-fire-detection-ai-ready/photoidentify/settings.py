import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# セキュリティ設定（環境変数から読む）
# ============================================================
# 本番（Render）では環境変数で上書きします。
# ローカル開発では環境変数がないため、下のデフォルト値が使われます。

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "local-dev-secret-key-for-development-only",
)

# 環境変数 DEBUG が "True" のときだけ True になります。
# Renderには DEBUG=False を設定します。
DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS",
    "127.0.0.1,localhost",
).split(",")

CSRF_TRUSTED_ORIGINS = os.environ.get(
    "CSRF_TRUSTED_ORIGINS",
    "http://127.0.0.1,http://localhost",
).split(",")

# AI推論のON/OFFスイッチ。
# Renderのメモリ不足でAIが動かない場合、
# 環境変数 ENABLE_AI=False にすると軽量デモ版として動きます。
ENABLE_AI = os.environ.get("ENABLE_AI", "True") == "True"


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'prediction',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise: 本番で静的ファイル（admin画面のCSSなど）を配信します。
    # SecurityMiddleware の直後に置くのがルールです。
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'photoidentify.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'photoidentify.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_TZ = True


# ============================================================
# 静的ファイル・メディアファイル設定
# ============================================================

STATIC_URL = 'static/'

# collectstatic の出力先です。Renderのビルドで使います。
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================================
# AIモデル設定
# ============================================================
# このDjangoアプリで使うAIモデルの保存場所をまとめています。
# prediction/models/ の中に .pt や .keras モデルを配置します。

AI_MODEL_DIR = BASE_DIR / "prediction" / "models"

# 自作Gion YOLOモデル
# 役割: 祇園町向けに作った fire / smoke 検出モデル
YOLO_MODEL_PATH = AI_MODEL_DIR / "gion_fire_yolov8n_finetune_v2_best.pt"

# 公開Fire-Smoke YOLOモデル
# 役割: smoke / fire の補助検出
PUBLIC_FIRE_SMOKE_YOLO_MODEL_PATH = AI_MODEL_DIR / "public_fire_smoke_yolov8n_best.pt"

# MobileNetV2系 画像分類モデル
# 役割: 画像全体を fire / normal / smoke に分類
CLASSIFICATION_MODEL_PATH = AI_MODEL_DIR / "260627model_gion_fire_MNV2.h5.keras"

# 画像分類モデルのクラス順
# 注意: 学習時のフォルダ順と一致している必要があります。
CLASSIFICATION_CLASS_NAMES = ["fire", "normal", "smoke"]
