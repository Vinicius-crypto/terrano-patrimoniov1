import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "segredo"
    
    if os.environ.get("FLASK_ENV") == "production":
        SQLALCHEMY_DATABASE_URI = os.environ.get(
            "DATABASE_URL",
            "postgresql://vinicius@terrano-patrimonio-server:XFmkbizvA2gL@terrano-patrimonio-server.postgres.database.azure.com:5432/terrano-patrimonio-database"
        )
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///db.sqlite3"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.getenv('HOME', ''), 'site/wwwroot/uploads/termos')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
