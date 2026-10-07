import os

os.environ["FLASK_ENV"] = "testing"
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

import bcrypt
import pytest

from app import app as flask_app
from models import db, Usuario

SENHA = "Senha123!"


def _criar_usuario(username, nivel):
    hash_senha = bcrypt.hashpw(SENHA.encode(), bcrypt.gensalt()).decode()
    db.session.add(Usuario(username=username, password_hash=hash_senha, nivel_acesso=nivel, ativo=True))
    db.session.commit()


@pytest.fixture()
def app():
    with flask_app.app_context():
        db.create_all()
        _criar_usuario("admin", 3)
        _criar_usuario("leitor", 1)
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def login(client):
    def _login(username="admin", senha=SENHA):
        return client.post("/login", data={"username": username, "senha": senha})
    return _login
