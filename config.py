import os

class Config:
    # Chave secreta (não compartilhe em produção!)
    SECRET_KEY = os.environ.get("SECRET_KEY") or "a3f5c2d1e4b8f7d9a0c3e2b1d4f6a8c9"
    
    # URL do PostgreSQL do Azure (com suas credenciais)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://uahaqxdyim:XFmkbizvA2gL@terrano-patrimonio-server.postgres.database.azure.com:5432/postgres"
    )
    
    # Correção obrigatória para Azure
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuração de uploads para Azure
    UPLOAD_FOLDER = os.path.join(os.getenv('HOME', ''), 'site/wwwroot/uploads/termos')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # Último deploy: {10-04-2025 e 20:37}