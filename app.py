"""
Sistema de Controle de Patrimônio - Terrano
Aplicação Flask com factory, CSRF, rate limit e armazenamento local de termos.
"""
import os
import re
import click
import bcrypt
from datetime import datetime
from flask import Flask, render_template
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()

from config import ProductionConfig, DevelopmentConfig, TestingConfig
from models import db, Usuario, Categoria
from views import init_routes
from logging_config_simple import structured_logger

csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=[])

CATEGORIAS_PADRAO = [
    ('Informática', 'Equipamentos de informática e tecnologia'),
    ('Mobiliário', 'Móveis e equipamentos de escritório'),
    ('Eletrodomésticos', 'Aparelhos eletrodomésticos'),
    ('Ferramentas', 'Ferramentas e equipamentos de trabalho'),
    ('Veículos', 'Veículos e equipamentos de transporte'),
    ('Equipamentos de Segurança', 'Equipamentos de segurança e proteção'),
    ('Equipamentos de Comunicação', 'Equipamentos de telecomunicações'),
    ('Outros', 'Outros tipos de equipamentos'),
]


def create_app(config_name=None):
    app = Flask(__name__)

    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object({
        'production': ProductionConfig,
        'testing': TestingConfig,
    }.get(config_name, DevelopmentConfig))

    if not app.config.get('SECRET_KEY'):
        raise RuntimeError("SECRET_KEY não definida no ambiente.")
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        raise RuntimeError("DATABASE_URL não definida no ambiente.")

    setup_upload_directories(app)

    db.init_app(app)
    Migrate(app, db)
    csrf.init_app(app)
    limiter.init_app(app)
    limiter.enabled = not app.config.get('TESTING', False)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "error"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    structured_logger.init_app(app)
    init_routes(app)
    app.view_functions['login'] = limiter.limit(
        "10 per minute", methods=["POST"]
    )(app.view_functions['login'])
    register_context_processors(app)
    register_error_handlers(app)
    register_security_headers(app)
    register_cli(app)

    return app


def setup_upload_directories(app):
    base = os.path.join(os.path.dirname(__file__), 'uploads')
    app.config['UPLOAD_FOLDER'] = os.path.join(base, 'termos')
    app.config['IMAGES_FOLDER'] = os.path.join(base, 'images')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['IMAGES_FOLDER'], exist_ok=True)


def register_context_processors(app):
    @app.context_processor
    def inject_globals():
        return {
            'datetime': datetime,
            'app_name': 'Controle de Patrimônio',
            'app_version': '2.0.0',
        }


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(429)
    def too_many_requests(error):
        return "Muitas tentativas. Aguarde um minuto e tente novamente.", 429

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f"Erro interno do servidor: {error}")
        return render_template('errors/500.html'), 500


def register_security_headers(app):
    @app.after_request
    def add_headers(response):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
        response.headers.setdefault('Referrer-Policy', 'same-origin')
        return response


def register_cli(app):
    @app.cli.command('create-admin')
    @click.option('--username', default='admin', show_default=True)
    @click.option('--password', envvar='ADMIN_PASSWORD', prompt=True,
                  hide_input=True, confirmation_prompt=True)
    def create_admin(username, password):
        """Cria ou promove um usuário administrador."""
        if len(password) < 8 or not re.search(r'\d', password) or not re.search(r'[A-Za-z]', password):
            raise click.ClickException("A senha precisa ter 8+ caracteres, com letras e números.")
        hash_senha = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        usuario = Usuario.query.filter_by(username=username).first()
        if usuario:
            usuario.password_hash = hash_senha
            usuario.nivel_acesso = 3
            usuario.ativo = True
        else:
            db.session.add(Usuario(
                username=username, password_hash=hash_senha, nivel_acesso=3,
                nome_completo='Administrador', ativo=True, created_at=datetime.utcnow(),
            ))
        db.session.commit()
        click.echo(f"Administrador '{username}' pronto.")

    @app.cli.command('seed-categorias')
    def seed_categorias():
        """Insere as categorias padrão que ainda não existem."""
        criadas = 0
        for nome, descricao in CATEGORIAS_PADRAO:
            if not Categoria.query.filter_by(nome=nome).first():
                db.session.add(Categoria(nome=nome, descricao=descricao))
                criadas += 1
        db.session.commit()
        click.echo(f"{criadas} categoria(s) criada(s).")


app = create_app()

if __name__ == '__main__':
    app.run(
        debug=app.config['DEBUG'],
        host=os.environ.get('FLASK_HOST', '127.0.0.1'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
    )
