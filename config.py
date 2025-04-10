import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "a3f5c2d1e4b8f7d9a0c3e2b1d4f6a8c9"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "postgresql://uahaqxdyim:XFmkbizvA2gL@terrano-patrimonio-server.postgres.database.azure.com:5432/postgres"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.getenv('HOME', ''), 'site/wwwroot/uploads/termos')  # Nova linha

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False