"""
Django settings for primexa_project.

First production-cut configuration
for Primexa Exchange deployment on exchange.primexaglobal.com / cPanel or supported Python hosting.
"""

from pathlib import Path
import os


# ==========================================================
# BASE DIRECTORY
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ==========================================================
# SECURITY
# ==========================================================

# Keep the secret in this file for the current first cut.
# Later we can move it to cPanel environment variables.

SECRET_KEY = "django-insecure-6o94vjwiu7b3zvgwuhq)j@+x01be@c**0o*w(x%8wh0w3zo((6"


# ==========================================================
# DEBUG
# ==========================================================

# PRODUCTION
DEBUG = os.getenv("PRIMEXA_PRODUCTION", "0") != "1"


# ==========================================================
# ALLOWED HOSTS
# ==========================================================

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "exchange.primexaglobal.com",
    "primexaglobal.com",
    "www.primexaglobal.com",
    "domainz.in",
    "www.domainz.in",
]


# ==========================================================
# CSRF TRUSTED ORIGINS
# ==========================================================

CSRF_TRUSTED_ORIGINS = [
    "https://exchange.primexaglobal.com",
    "https://primexaglobal.com",
    "https://www.primexaglobal.com",
    "https://domainz.in",
    "https://www.domainz.in",
]


# ==========================================================
# APPLICATIONS
# ==========================================================

INSTALLED_APPS = [

    "django.contrib.admin",

    "django.contrib.auth",

    "django.contrib.contenttypes",

    "django.contrib.sessions",

    "django.contrib.messages",

    "django.contrib.staticfiles",

    "django.contrib.sitemaps",

    # ------------------------------------------------------
    # PRIMEXA APPLICATIONS
    # ------------------------------------------------------

    "users",

    "exchange",
]


# ==========================================================
# MIDDLEWARE
# ==========================================================

MIDDLEWARE = [

    "django.middleware.security.SecurityMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",

    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "primexa_project.middleware.AuthenticatedPageNoIndexMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",

    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ==========================================================
# URL CONFIGURATION
# ==========================================================

ROOT_URLCONF = "primexa_project.urls"


# ==========================================================
# TEMPLATES
# ==========================================================

TEMPLATES = [

    {
        "BACKEND":
            "django.template.backends.django.DjangoTemplates",

        "DIRS": [
            BASE_DIR / "templates",
        ],

        "APP_DIRS": True,

        "OPTIONS": {

            "context_processors": [

                "django.template.context_processors.request",

                "django.contrib.auth.context_processors.auth",

                "django.contrib.messages.context_processors.messages",

            ],
        },
    },
]


# ==========================================================
# WSGI
# ==========================================================

WSGI_APPLICATION = "primexa_project.wsgi.application"


# ==========================================================
# DATABASE
# ==========================================================

# ----------------------------------------------------------
# PRODUCTION MYSQL
#
# cPanel / MySQL database for Primexa Exchange.
# The password is intentionally left as a placeholder.
# ----------------------------------------------------------

if DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": "primexag_datap",
            "USER": "primexag_admin",
            "PASSWORD": os.getenv("PRIMEXA_DB_PASSWORD", ""),
            "HOST": "localhost",
            "PORT": "3306",
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }


# ==========================================================
# PASSWORD VALIDATION
# ==========================================================

AUTH_PASSWORD_VALIDATORS = [

    {
        "NAME":
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator",
    },

    {
        "NAME":
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator",
    },
]


# ==========================================================
# INTERNATIONALIZATION
# ==========================================================

LANGUAGE_CODE = "en-us"


# India
TIME_ZONE = "Asia/Kolkata"


USE_I18N = True

USE_TZ = True


# ==========================================================
# STATIC FILES
# ==========================================================

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"


# ----------------------------------------------------------
# Optional project-level static directory
# ----------------------------------------------------------

# Only register the project-level static directory if it exists.
# This prevents staticfiles.W004 when the directory is absent.
STATICFILES_DIRS = [
    BASE_DIR / "static",
] if (BASE_DIR / "static").exists() else []


# ==========================================================
# MEDIA FILES
# ==========================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"


# ==========================================================
# PROTECTED MEDIA
# ==========================================================

# Confidential Primexa CAD / engineering files.
#
# These files should NOT be exposed as normal public files.
# Access should go through Django permission-controlled
# download views.

PROTECTED_MEDIA_ROOT = BASE_DIR / "protected_media"


# ==========================================================
# DEFAULT PRIMARY KEY
# ==========================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ==========================================================
# CUSTOM USER MODEL
# ==========================================================

AUTH_USER_MODEL = "users.User"


# ==========================================================
# LOGIN / LOGOUT
# ==========================================================

LOGIN_URL = "login"

LOGIN_REDIRECT_URL = "dashboard"

LOGOUT_REDIRECT_URL = "login"


# ==========================================================
# PRIMEXA WEBSITE URL
# ==========================================================

SITE_URL = "https://exchange.primexaglobal.com" if not DEBUG else "http://127.0.0.1:8000"


# ==========================================================
# EMAIL CONFIGURATION
# ==========================================================

# ----------------------------------------------------------
# HOSTINGER SMTP
#
# Port 465 uses SSL.
# TLS must remain False.
# ----------------------------------------------------------

EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend"
)

EMAIL_HOST = "smtp.hostinger.com"

EMAIL_PORT = 465

EMAIL_USE_SSL = True

EMAIL_USE_TLS = False


# ----------------------------------------------------------
# PRIMEXA EMAIL ACCOUNT
# ----------------------------------------------------------

EMAIL_HOST_USER = os.getenv("PRIMEXA_EMAIL_USER", "no-reply@primexaglobal.com")


# IMPORTANT:
# Put the CURRENT password of the Hostinger mailbox here.
#
# Do NOT use the password previously exposed in the chat.
# Change the mailbox password in Hostinger first.
#
EMAIL_HOST_PASSWORD = os.getenv("PRIMEXA_EMAIL_PASSWORD", "Wqwertyuiop@1234567890")


# ----------------------------------------------------------
# DEFAULT SENDER
# ----------------------------------------------------------

DEFAULT_FROM_EMAIL = (
    "Primexa <no-reply@primexaglobal.com>"
)

SERVER_EMAIL = DEFAULT_FROM_EMAIL


# ----------------------------------------------------------
# SMTP TIMEOUT
# ----------------------------------------------------------

EMAIL_TIMEOUT = 30

if DEBUG and os.getenv("PRIMEXA_LOCAL_EMAIL_SMTP", "0") != "1":
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# ==========================================================
# PASSWORD RESET
# ==========================================================

# Password reset links remain valid for 1 hour.

PASSWORD_RESET_TIMEOUT = 60 * 60


# ==========================================================
# SESSION SECURITY
# ==========================================================

# Enable only when the deployment proxy overwrites this header.
# Otherwise a client could supply a spoofed X-Forwarded-For value.
TRUST_X_FORWARDED_FOR = (
    os.getenv("PRIMEXA_TRUST_X_FORWARDED_FOR", "0") == "1"
)

SESSION_COOKIE_AGE = 60 * 60 * 8

SESSION_SAVE_EVERY_REQUEST = False

SESSION_EXPIRE_AT_BROWSER_CLOSE = False


# ==========================================================
# PRODUCTION HTTPS SECURITY
# ==========================================================

if not DEBUG:

    # ------------------------------------------------------
    # Force HTTPS
    # ------------------------------------------------------

    SECURE_SSL_REDIRECT = True


    # ------------------------------------------------------
    # cPanel / Passenger / proxy HTTPS
    # ------------------------------------------------------

    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )


    # ------------------------------------------------------
    # Secure cookies
    # ------------------------------------------------------

    SESSION_COOKIE_SECURE = True

    CSRF_COOKIE_SECURE = True


    # ------------------------------------------------------
    # HTTP-only session cookie
    # ------------------------------------------------------

    SESSION_COOKIE_HTTPONLY = True


    # ------------------------------------------------------
    # Security headers
    # ------------------------------------------------------

    SECURE_CONTENT_TYPE_NOSNIFF = True

    SECURE_BROWSER_XSS_FILTER = True

    X_FRAME_OPTIONS = "DENY"

    # HSTS - keep enabled only when HTTPS is working correctly.
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = False

    SECURE_REFERRER_POLICY = "same-origin"


else:

    SECURE_SSL_REDIRECT = False

    SESSION_COOKIE_SECURE = False

    CSRF_COOKIE_SECURE = False


# ==========================================================
# FILE UPLOAD LIMITS
# ==========================================================

# 50 MB request limit.
#
# Actual cPanel / PHP / Passenger limits may also need to
# be adjusted depending on the hosting plan.

DATA_UPLOAD_MAX_MEMORY_SIZE = (
    50 * 1024 * 1024
)

FILE_UPLOAD_MAX_MEMORY_SIZE = (
    50 * 1024 * 1024
)


# ==========================================================
# ADMIN EMAIL
# ==========================================================

ADMINS = [

    (
        "Primexa Admin",
        "founder@firstyearbiz.in",
    ),

]

# STATIC_URL=os.path.join(BASE_DIR, 'staticfiles')

# ==========================================================
# PRODUCTION CHECKLIST
# ==========================================================
#
# Before going live:
#
# 1. Change the exposed Hostinger mailbox password.
#
# 2. Put the NEW password above:
#
#    EMAIL_HOST_PASSWORD = "..."
#
# 3. Make sure domainz.in has SSL/HTTPS enabled.
#
# 4. Run:
#
#       python manage.py check --deploy
#
# 5. Run:
#
#       python manage.py makemigrations
#
# 6. Run:
#
#       python manage.py migrate
#
# 7. Run:
#
#       python manage.py collectstatic
#
# 8. Test:
#
#       python manage.py runserver
#
# 9. Test password reset.
#
# 10. Test Primexa notification emails.
#
# 11. Upload application to cPanel.
#
# 12. Configure Python application / Passenger.
#
# ==========================================================
