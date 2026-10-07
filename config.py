import os
import secrets


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Ative atrás de HTTPS; com True o login falha em HTTP puro.
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"


class DevelopmentConfig(Config):
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    # Sem SECRET_KEY definida, as sessões são invalidadas a cada reinício.
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)


class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY")


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    WTF_CSRF_ENABLED = False
