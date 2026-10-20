"""Application settings, read from environment variables.

Pick a profile with APP_ENV=development | testing | production (default: development).
Production refuses to start without the secrets it needs (OWASP A02 / A03).
"""
import os
from datetime import timedelta


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _env_list(name, default=()):
    value = os.environ.get(name)
    if not value:
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


class BaseConfig:
    ENV_NAME = "base"
    DEBUG = False
    TESTING = False

    # Secrets: never hardcode these in production; set them in the environment.
    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    # Fernet key (urlsafe base64, 32 bytes) for encrypting sensitive columns such as MFA secrets.
    ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///trendify.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Reject request bodies over 5 MB (product image uploads are the largest legitimate request).
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # --- Authentication (A06) -------------------------------------------------
    # JWTs live in HttpOnly cookies (not readable by JavaScript) with CSRF double-submit protection.
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_SAMESITE = "Strict"
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_SESSION_COOKIE = False
    JWT_ERROR_MESSAGE_KEY = "error"

    LOGIN_MAX_FAILED_ATTEMPTS = 5
    LOGIN_LOCKOUT_PERIOD = timedelta(minutes=15)
    EMAIL_TOKEN_EXPIRES = timedelta(hours=24)
    PASSWORD_RESET_EXPIRES = timedelta(minutes=30)
    MFA_ISSUER = "Trendify"

    # --- Rate limiting (A05 / A06) ---------------------------------------------
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = "300 per minute"
    RATELIMIT_HEADERS_ENABLED = True

    # --- CORS (A02): only trusted frontend origins ------------------------------
    CORS_ORIGINS = _env_list("CORS_ORIGINS")

    # Number of reverse proxies in front of the app (for correct client IPs and HTTPS detection).
    TRUSTED_PROXY_COUNT = int(os.environ.get("TRUSTED_PROXY_COUNT", "0"))
    FORCE_HTTPS = _env_bool("FORCE_HTTPS", False)

    # --- URLs --------------------------------------------------------------------
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    # Public base URL of this API, used for the Pesapal IPN callback.
    API_PUBLIC_URL = os.environ.get("API_PUBLIC_URL", "http://localhost:5173/api").rstrip("/")

    # --- Email -------------------------------------------------------------------
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = _env_bool("MAIL_USE_TLS", True)
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "Trendify <no-reply@trendify.local>")
    # Where security alerts are emailed (optional).
    SECURITY_ALERT_EMAIL = os.environ.get("SECURITY_ALERT_EMAIL")

    # --- Payments (Pesapal API 3.0) ------------------------------------------------
    # "pesapal" for real payments, "simulated" for local development without credentials.
    PAYMENT_PROVIDER = os.environ.get("PAYMENT_PROVIDER", "pesapal")
    PESAPAL_ENV = os.environ.get("PESAPAL_ENV", "sandbox")  # sandbox | live
    PESAPAL_CONSUMER_KEY = os.environ.get("PESAPAL_CONSUMER_KEY")
    PESAPAL_CONSUMER_SECRET = os.environ.get("PESAPAL_CONSUMER_SECRET")
    PESAPAL_IPN_ID = os.environ.get("PESAPAL_IPN_ID")
    CURRENCY = os.environ.get("CURRENCY", "USD")

    MAX_ITEMS_PER_ORDER = 50
    MAX_QUANTITY_PER_ITEM = 10

    @classmethod
    def validate(cls):
        """Raise if the configuration is unsafe for this profile."""


class DevelopmentConfig(BaseConfig):
    ENV_NAME = "development"
    DEBUG = _env_bool("FLASK_DEBUG", True)
    SECRET_KEY = BaseConfig.SECRET_KEY or "dev-only-insecure-key-change-me"
    JWT_COOKIE_SECURE = False  # local development runs over plain http://localhost
    CORS_ORIGINS = BaseConfig.CORS_ORIGINS or ["http://localhost:5173", "http://127.0.0.1:5173"]
    PAYMENT_PROVIDER = os.environ.get("PAYMENT_PROVIDER", "simulated")


class TestingConfig(BaseConfig):
    ENV_NAME = "testing"
    TESTING = True
    SECRET_KEY = "testing-secret-key-not-for-real-use-0123456789"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    JWT_COOKIE_SECURE = False
    CORS_ORIGINS = ["http://localhost:5173"]
    PAYMENT_PROVIDER = "simulated"
    MAIL_SERVER = None


class ProductionConfig(BaseConfig):
    ENV_NAME = "production"
    FORCE_HTTPS = _env_bool("FORCE_HTTPS", True)

    @classmethod
    def validate(cls):
        problems = []
        if not cls.SECRET_KEY or len(cls.SECRET_KEY) < 32:
            problems.append("SECRET_KEY must be set to a random value of at least 32 characters")
        if not cls.ENCRYPTION_KEY:
            problems.append("ENCRYPTION_KEY must be set (generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\")")
        if not cls.CORS_ORIGINS:
            problems.append("CORS_ORIGINS must list the trusted frontend origin(s)")
        if any(o == "*" or not o.startswith("https://") for o in cls.CORS_ORIGINS):
            problems.append("CORS_ORIGINS must only contain explicit https:// origins")
        if cls.PAYMENT_PROVIDER != "pesapal":
            problems.append("PAYMENT_PROVIDER must be 'pesapal' in production")
        elif not (cls.PESAPAL_CONSUMER_KEY and cls.PESAPAL_CONSUMER_SECRET):
            problems.append("PESAPAL_CONSUMER_KEY and PESAPAL_CONSUMER_SECRET must be set")
        if problems:
            raise RuntimeError("Unsafe production configuration:\n  - " + "\n  - ".join(problems))


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name=None):
    name = (name or os.environ.get("APP_ENV") or "development").lower()
    if name not in CONFIGS:
        raise RuntimeError(f"Unknown APP_ENV {name!r}; use one of {', '.join(CONFIGS)}")
    return CONFIGS[name]
