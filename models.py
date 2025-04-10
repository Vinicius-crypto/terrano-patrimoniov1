from app import db  # Essa importação será feita depois que o db for definido em app.py
from flask_login import UserMixin

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    nivel_acesso = db.Column(db.Integer, default=1)
    
    def __repr__(self):
        return f"<Usuario {self.username}>"

class Equipamento(db.Model):
    id_interno = db.Column(db.Integer, primary_key=True)
    id_publico = db.Column(db.String(20), unique=True, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(50))
    num_serie = db.Column(db.String(50), unique=True)
    data_aquisicao = db.Column(db.Date, nullable=False)
    localizacao = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='Estocado')
    responsavel = db.Column(db.String(100))
    ultima_manutencao = db.Column(db.Date)
    valor = db.Column(db.Float)
    observacoes = db.Column(db.Text)
    SPE = db.Column(db.String(50))
    termo_pdf_path = db.Column(db.String(200))
    
    def __repr__(self):
        return f"<Equipamento {self.id_publico}>"
