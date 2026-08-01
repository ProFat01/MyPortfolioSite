"""
Django settings for portfolio_project.
"""

from pathlib import Path
import os
import environ
# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY — change this in production!
# Reads from the environment first so PythonAnywhere (or any host) can set
# a real secret key without editing this file; falls back to the original
# placeholder so nothing breaks if the env var isn't set yet.
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="8jsi6-@#yj&=eekufua#f4hkpo*u495p7c4r1fpv1r046^yk-1",
)

# Set to False in production
# Detect whether we're running on PythonAnywhere
ON_PYTHONANYWHERE = "PYTHONANYWHERE_SITE" in os.environ

if ON_PYTHONANYWHERE:
    DEBUG = False
    ALLOWED_HOSTS = ["DevProf.pythonanywhere.com"]
else:
    DEBUG = True
    ALLOWED_HOSTS = [
        "127.0.0.1",
        "localhost",
    ]
# -------------------------------------------------
# Site identity — used in email templates, SEO meta tags, and sitemap URLs
# -------------------------------------------------
SITE_NAME = os.environ.get('SITE_NAME', 'Saidu — Portfolio')
SITE_URL = os.environ.get('SITE_URL', 'https://DevProf.pythonanywhere.com')

# -------------------------------------------------
# Installed apps
# -------------------------------------------------
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'portfolio.apps.PortfolioConfig',           # Our custom app
]

SITE_ID = 1

# jazzmin settings
JAZZMIN_SETTINGS = {
    "welcome_sign": "Welcome Saidu",
    "copyright": "DevProf Technologies",
    "site_title": "Saidu Admin",
    "site_header": "Saidu Portfolio",
    "site_brand": "DevProf",

    "site_logo": "img/logo.png",
    "login_logo": "img/logo.png",
    "site_logo_classes": "img-circle",
}


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'portfolio_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Look for templates inside each app's "templates" folder
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

WSGI_APPLICATION = 'portfolio_project.wsgi.application'

# -------------------------------------------------
# Database — SQLite is fine for a personal portfolio
# -------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalisation
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# -------------------------------------------------
# Static files  (CSS, JavaScript, images)
# -------------------------------------------------

STATIC_URL = '/static/'
# Where collectstatic will copy everything in production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# -------------------------------------------------
# Media files  (user-uploaded images)
# -------------------------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# -------------------------------------------------
# Email — powers the Contact form's notification + confirmation emails.
#
# Local/dev default: prints emails to the console, so nothing needs to
# be configured to test the flow locally.
#
# Production (PythonAnywhere or any SMTP host): set these environment
# variables and nothing else needs to change:
#
#   DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
#   EMAIL_HOST=smtp.gmail.com          (or your provider's SMTP host)
#   EMAIL_PORT=587
#   EMAIL_USE_TLS=True
#   EMAIL_HOST_USER=you@example.com
#   EMAIL_HOST_PASSWORD=your-app-password
#   DEFAULT_FROM_EMAIL=you@example.com
#   CONTACT_RECIPIENT_EMAIL=you@example.com   (where enquiries land — can differ from the sender)
# -------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'alsaeedn159@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Saidu Portfolio <alsaeedn159@gmail.com>')

# Who receives the "new contact form message" notification.
CONTACT_RECIPIENT_EMAIL = os.environ.get('CONTACT_RECIPIENT_EMAIL', DEFAULT_FROM_EMAIL)

# Name used to sign the visitor confirmation email.
CONTACT_OWNER_NAME = os.environ.get('CONTACT_OWNER_NAME', 'Saidu')

# Set to False to disable the automatic visitor confirmation email
# while still keeping the owner notification email active.
CONTACT_SEND_CONFIRMATION = os.environ.get('CONTACT_SEND_CONFIRMATION', 'True') == 'True'