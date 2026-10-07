"""
Modelos de dados do Sistema de Controle de Patrimônio
Separado do app.py para melhor organização
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    nivel_acesso = db.Column(db.Integer, default=1)
    email = db.Column(db.String(120), nullable=True)
    nome_completo = db.Column(db.String(200), nullable=True)
    departamento = db.Column(db.String(100), nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relacionamentos
    equipamentos_criados = db.relationship('Equipamento', foreign_keys='Equipamento.created_by', backref='criado_por')
    equipamentos_editados = db.relationship('Equipamento', foreign_keys='Equipamento.updated_by', backref='editado_por')
    
    @property
    def is_admin(self):
        """Retorna True se o usuário for administrador (nível 3)"""
        return self.nivel_acesso == 3

class Categoria(db.Model):
    __tablename__ = 'categoria'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    icone = db.Column(db.String(50), nullable=True)  # Nome do ícone/emoji
    cor = db.Column(db.String(7), nullable=True)     # Cor hex #ff0000
    descricao = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    equipamentos = db.relationship('Equipamento', backref='categoria_obj', lazy=True)

class Fornecedor(db.Model):
    __tablename__ = 'fornecedor'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    cnpj = db.Column(db.String(18), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    endereco = db.Column(db.Text, nullable=True)
    contato_principal = db.Column(db.String(200), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    
    # Relacionamentos
    equipamentos = db.relationship('Equipamento', backref='fornecedor_obj', lazy=True)

class ManutencaoProgramada(db.Model):
    __tablename__ = 'manutencao_programada'
    
    id = db.Column(db.Integer, primary_key=True)
    equipamento_id = db.Column(db.Integer, db.ForeignKey('equipamento.id_interno'), nullable=False)
    tipo = db.Column(db.String(100), nullable=False)  # Preventiva, Corretiva, Emergencial
    descricao = db.Column(db.Text, nullable=False)
    data_programada = db.Column(db.Date, nullable=False)
    data_realizada = db.Column(db.Date, nullable=True)
    responsavel_tecnico = db.Column(db.String(200), nullable=True)
    custo_estimado = db.Column(db.Float, nullable=True, default=0.0)
    custo_real = db.Column(db.Float, nullable=True, default=0.0)
    status = db.Column(db.String(50), default='Agendada')  # Agendada, Em Andamento, Concluída, Cancelada
    observacoes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)

class HistoricoEquipamento(db.Model):
    __tablename__ = 'historico_equipamento'
    
    id = db.Column(db.Integer, primary_key=True)
    equipamento_id = db.Column(db.Integer, db.ForeignKey('equipamento.id_interno'), nullable=False)
    acao = db.Column(db.String(100), nullable=False)  # Criado, Editado, Movido, Manutenção, etc.
    campo_alterado = db.Column(db.String(100), nullable=True)
    valor_anterior = db.Column(db.Text, nullable=True)
    valor_novo = db.Column(db.Text, nullable=True)
    descricao = db.Column(db.Text, nullable=True)
    data_acao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # Suporte IPv6

class Notificacao(db.Model):
    __tablename__ = 'notificacao'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # info, warning, error, success
    lida = db.Column(db.Boolean, default=False)
    link_acao = db.Column(db.String(200), nullable=True)  # URL para ação relacionada
    equipamento_id = db.Column(db.Integer, db.ForeignKey('equipamento.id_interno'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    lida_em = db.Column(db.DateTime, nullable=True)

class Equipamento(db.Model):
    __tablename__ = 'equipamento'
    
    id_interno = db.Column(db.Integer, primary_key=True)
    id_publico = db.Column(db.String(20), unique=True, nullable=False)
    
    # Informações Básicas
    tipo = db.Column(db.String(100), nullable=False)
    marca = db.Column(db.String(100), nullable=True)
    modelo = db.Column(db.String(100), nullable=True)
    num_serie = db.Column(db.String(100), nullable=True, unique=True)
    
    # Informações Financeiras
    data_aquisicao = db.Column(db.Date, nullable=True)
    valor = db.Column(db.Float, nullable=True, default=0.0)
    valor_residual = db.Column(db.Float, nullable=True, default=0.0)
    vida_util_anos = db.Column(db.Integer, nullable=True, default=5)
    valor_depreciado = db.Column(db.Float, nullable=True, default=0.0)  # Calculado automaticamente
    
    # Localização e Responsabilidade
    localizacao = db.Column(db.String(200), nullable=True)
    responsavel = db.Column(db.String(100), nullable=True)
    centro_custo = db.Column(db.String(100), nullable=True)
    departamento = db.Column(db.String(100), nullable=True)
    
    # Status e Manutenção
    status = db.Column(db.String(50), nullable=False, default='Estocado')
    condicao = db.Column(db.String(50), nullable=True, default='Novo')  # Novo, Usado, Danificado, Obsoleto
    ultima_manutencao = db.Column(db.Date, nullable=True)
    proxima_manutencao = db.Column(db.Date, nullable=True)  # Calculado automaticamente
    
    # Garantia e Fornecedor
    garantia_ate = db.Column(db.Date, nullable=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedor.id'), nullable=True)
    nota_fiscal = db.Column(db.String(100), nullable=True)
    
    # Categorização
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=True)
    subcategoria = db.Column(db.String(100), nullable=True)
    tags = db.Column(db.Text, nullable=True)  # JSON: ["urgente", "critico", "novo"]
    
    # Identificação Moderna
    codigo_barras = db.Column(db.String(100), nullable=True, unique=True)
    qr_code = db.Column(db.Text, nullable=True)  # QR Code gerado automaticamente
    rfid_tag = db.Column(db.String(100), nullable=True, unique=True)
    
    # Mídia e Documentos
    imagem_url = db.Column(db.String(500), nullable=True)
    termo_pdf_path = db.Column(db.String(500), nullable=True)
    manual_url = db.Column(db.String(500), nullable=True)
    
    # Campos Legados (manter compatibilidade)
    SPE = db.Column(db.String(50), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    
    # Campos Técnicos (IoT Future)
    especificacoes_tecnicas = db.Column(db.Text, nullable=True)  # JSON com specs técnicas
    configuracao = db.Column(db.Text, nullable=True)  # JSON com configurações
    
    # Auditoria e Controle
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    
    # Controle de Estado
    ativo = db.Column(db.Boolean, default=True)
    bloqueado = db.Column(db.Boolean, default=False)  # Para equipamentos em investigação/auditoria
    motivo_bloqueio = db.Column(db.String(200), nullable=True)
    
    # Relacionamentos
    historicos = db.relationship('HistoricoEquipamento', backref='equipamento', lazy=True, cascade='all, delete-orphan')
    manutencoes = db.relationship('ManutencaoProgramada', backref='equipamento', lazy=True, cascade='all, delete-orphan')
    notificacoes = db.relationship('Notificacao', backref='equipamento', lazy=True)
    
    def __repr__(self):
        return f'<Equipamento {self.id_publico}: {self.tipo}>'
    
    def to_dict(self):
        """Converte o equipamento para dicionário (para API JSON)"""
        return {
            'id_interno': self.id_interno,
            'id_publico': self.id_publico,
            'tipo': self.tipo,
            'marca': self.marca,
            'modelo': self.modelo,
            'num_serie': self.num_serie,
            'status': self.status,
            'localizacao': self.localizacao,
            'responsavel': self.responsavel,
            'valor': self.valor,
            'data_aquisicao': self.data_aquisicao.isoformat() if self.data_aquisicao else None,
            'garantia_ate': self.garantia_ate.isoformat() if self.garantia_ate else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'categoria': self.categoria_obj.nome if self.categoria_obj else None,
            'fornecedor': self.fornecedor_obj.nome if self.fornecedor_obj else None
        }
    
    @property
    def dias_garantia_restante(self):
        """Calcula quantos dias restam de garantia"""
        if not self.garantia_ate:
            return None
        return (self.garantia_ate - datetime.now().date()).days
    
    @property
    def valor_atual(self):
        """Calcula o valor atual considerando depreciação"""
        if not self.valor or not self.data_aquisicao or not self.vida_util_anos:
            return self.valor or 0
            
        anos_uso = (datetime.now().date() - self.data_aquisicao).days / 365.25
        if anos_uso >= self.vida_util_anos:
            return self.valor_residual or 0
            
        depreciacao_anual = (self.valor - (self.valor_residual or 0)) / self.vida_util_anos
        return max(self.valor - (depreciacao_anual * anos_uso), self.valor_residual or 0)
    
    @property
    def precisa_manutencao(self):
        """Verifica se precisa de manutenção baseado na data"""
        if not self.proxima_manutencao:
            return False
        return datetime.now().date() >= self.proxima_manutencao