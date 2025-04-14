import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "XFmkbizvA2gL"
    
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(os.getenv('HOME', ''), 'site/wwwroot/uploads/termos')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
