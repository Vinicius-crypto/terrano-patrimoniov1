import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "XFmkbizvA2gL"

    # Banco de dados via variável de ambiente (segurança e flexibilidade)
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///db.sqlite3"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.getenv('HOME', ''), 'site/wwwroot/uploads/termos')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
