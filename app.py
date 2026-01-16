"""
Sistema de Controle de Patrimônio - Terrano v1 (Refatorado)
Aplicação Flask modular com arquitetura limpa
"""
import os
import bcrypt
from datetime import datetime
from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager

# Carregar variáveis de ambiente em desenvolvimento
if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()

# Importações dos módulos
from config import ProductionConfig, DevelopmentConfig
from models import db, Usuario
from views import init_routes
from logging_config_simple import structured_logger

# ============= INICIALIZAÇÃO DA APLICAÇÃO =============
def create_app(config_name=None):
    """Factory function para criar a aplicação Flask"""
    
    app = Flask(__name__)
    
    # Configuração
    if config_name == 'production' or os.environ.get('FLASK_ENV') == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)
    
    # Correção para PostgreSQL no Azure
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        raise RuntimeError("⚠️ DATABASE_URL não definida no ambiente!")

    uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    if uri and uri.startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = uri.replace('postgres://', 'postgresql://', 1)

    # Configurar diretórios de upload
    setup_upload_directories(app)
    
    # Configurar Azure Blob Storage
    setup_azure_storage(app)
    
    # Inicializar extensões
    db.init_app(app)
    
    migrate = Migrate(app, db)
    
    # Configurar Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "error"
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))
    
    # Configurar logging estruturado
    structured_logger.init_app(app)
    
    # Registrar rotas
    init_routes(app)
    
    # Registrar context processors
    register_context_processors(app)
    
    # Configurar hooks da aplicação
    setup_app_hooks(app)
    
    return app

def setup_upload_directories(app):
    """Configurar diretórios de upload"""
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'termos')
    IMAGES_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'images')
    
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(IMAGES_FOLDER, exist_ok=True)
    
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['IMAGES_FOLDER'] = IMAGES_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB máximo

def setup_azure_storage(app):
    """Configurar Azure Blob Storage"""
    from azure.storage.blob import BlobServiceClient
    
    BLOB_CONTAINER = 'termos'
    blob_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    
    # Para desenvolvimento: usar armazenamento local se Azure não configurado
    USE_LOCAL_STORAGE = not blob_connection_string or blob_connection_string == "DefaultEndpointsProtocol=https;AccountName=devaccount;AccountKey=fake;EndpointSuffix=core.windows.net"
    
    if not USE_LOCAL_STORAGE:
        try:
            blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
            container_client = blob_service_client.get_container_client(BLOB_CONTAINER)
            container_client.create_container()
        except Exception:
            pass  # container já existe
        
        app.config['BLOB_SERVICE_CLIENT'] = blob_service_client
        app.config['CONTAINER_CLIENT'] = container_client
    else:
        print("⚠️  Modo desenvolvimento: usando armazenamento local para PDFs")
        app.config['BLOB_SERVICE_CLIENT'] = None
        app.config['CONTAINER_CLIENT'] = None
    
    app.config['USE_LOCAL_STORAGE'] = USE_LOCAL_STORAGE

def register_context_processors(app):
    """Registrar context processors para templates"""
    
    @app.context_processor
    def inject_datetime():
        return {'datetime': datetime}
    
    @app.context_processor
    def inject_app_info():
        return {
            'app_name': 'Controle de Patrimônio',
            'app_version': '1.0.0'
        }

def setup_app_hooks(app):
    """Configurar hooks da aplicação"""
    
    def create_admin_user():
        """Criar usuário admin se não existir"""
        if not Usuario.query.filter_by(username='admin').first():
            hash_senha = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            admin = Usuario(
                username='admin', 
                password_hash=hash_senha, 
                nivel_acesso=3, 
                nome_completo='Administrador do Sistema',
                ativo=True,
                created_at=datetime.utcnow()
            )
            db.session.add(admin)
            db.session.commit()
            app.logger.info("Usuário admin criado: admin / admin123")
    
    # Executar criação de usuário admin na inicialização
    with app.app_context():
        db.create_all()
        create_admin_user()
    
    @app.errorhandler(404)
    def not_found(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        app.logger.error(f"Erro interno do servidor: {error}")
        return render_template('errors/500.html'), 500

# ============= CRIAÇÃO DA APLICAÇÃO =============
app = create_app()

# ============= INICIALIZAÇÃO DO BANCO DE DADOS =============
with app.app_context():
    try:
        db.create_all()
        app.logger.info("Banco de dados inicializado com sucesso")
    except Exception as e:
        app.logger.error(f"Erro ao inicializar banco de dados: {e}")

# ============= EXECUÇÃO DO SERVIDOR =============
if __name__ == '__main__':
    # Configurações específicas para desenvolvimento
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    app.logger.info(f"Iniciando servidor Flask em {host}:{port} (debug={debug})")
    app.run(debug=debug, host=host, port=port)