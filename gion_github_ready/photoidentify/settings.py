import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-local-dev-only-change-me')

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

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

STATIC_URL = 'static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

AI_MODEL_DIR = BASE_DIR / 'prediction' / 'models'

CLASSIFICATION_MODEL_PATH = AI_MODEL_DIR / '260627model_gion_fire_MNV2.h5.keras'
YOLO_MODEL_PATH = AI_MODEL_DIR / 'gion_fire_yolov8n_finetune_v2_best.pt'

CLASSIFICATION_CLASS_NAMES = [
    'fire',
    'normal',
    'smoke',
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================================
# AIモデル設定
# ============================================================
# このDjangoアプリで使うAIモデルの保存場所をまとめています。
# prediction/models/ の中に .pt や .keras モデルを配置します。

AI_MODEL_DIR = BASE_DIR / "prediction" / "models"

# 自作Gion YOLOモデル
# 役割:
# - 祇園町向けに作った fire / smoke 検出モデル
# - 火や煙の基本検出に使います。
YOLO_MODEL_PATH = AI_MODEL_DIR / "gion_fire_yolov8n_finetune_v2_best.pt"

# 公開Fire-Smoke YOLOモデル
# 役割:
# - 追加した公開モデル
# - smoke / fire の補助検出に使います。
PUBLIC_FIRE_SMOKE_YOLO_MODEL_PATH = AI_MODEL_DIR / "public_fire_smoke_yolov8n_best.pt"

# MobileNetV2系 画像分類モデル
# 役割:
# - 画像全体を fire / normal / smoke に分類します。
CLASSIFICATION_MODEL_PATH = AI_MODEL_DIR / "260627model_gion_fire_MNV2.h5.keras"

# 画像分類モデルのクラス順
# 注意:
# - 学習時のフォルダ順と一致している必要があります。
# - 結果が明らかにズレる場合は、この順番を疑います。
CLASSIFICATION_CLASS_NAMES = ["fire", "normal", "smoke"]












