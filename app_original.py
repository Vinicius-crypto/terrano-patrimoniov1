import os
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, Response
import qrcode
from PIL import Image
import uuid

# Carregar variáveis de ambiente em desenvolvimento
if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import bcrypt
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from datetime import datetime
from azure.storage.blob import BlobServiceClient
from io import BytesIO


# ============= INICIALIZAÇÃO =============
from config import ProductionConfig, DevelopmentConfig

app = Flask(__name__)
app.config.from_object(ProductionConfig if os.environ.get('FLASK_ENV') == 'production' else DevelopmentConfig)




# Correção para PostgreSQL no Azure

if not app.config.get('SQLALCHEMY_DATABASE_URI'):
    raise RuntimeError("⚠️ DATABASE_URL não definida no ambiente!")

uri = app.config.get('SQLALCHEMY_DATABASE_URI')
if uri and uri.startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = uri.replace('postgres://', 'postgresql://', 1)

# Caminho relativo ao diretório do app
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'termos')
IMAGES_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'images')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMAGES_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['IMAGES_FOLDER'] = IMAGES_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB máximo

# Extensões permitidas para upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Configuração do Azure Blob Storage (com fallback para desenvolvimento)
BLOB_CONTAINER = 'termos'
blob_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

# Para desenvolvimento: usar armazenamento local se Azure não configurado
USE_LOCAL_STORAGE = not blob_connection_string or blob_connection_string == "DefaultEndpointsProtocol=https;AccountName=devaccount;AccountKey=fake;EndpointSuffix=core.windows.net"

if not USE_LOCAL_STORAGE:
    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    container_client = blob_service_client.get_container_client(BLOB_CONTAINER)
    try:
        container_client.create_container()
    except Exception:
        pass  # container já existe
else:
    print("⚠️  Modo desenvolvimento: usando armazenamento local para PDFs")
    blob_service_client = None
    container_client = None


db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "error"

# ============= MODELOS =============
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

# ============= CONFIGURAÇÕES =============
@app.before_request
def criar_admin_uma_vez():
    if not hasattr(app, 'admin_criado'):
        if not Usuario.query.filter_by(username='admin').first():
            hash_senha = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            admin = Usuario(username='admin', password_hash=hash_senha, nivel_acesso=3, nome_completo='Administrador do Sistema')
            db.session.add(admin)
            db.session.commit()
            print("Usuário admin criado: admin / admin123")
        app.admin_criado = True

# ============= LOGIN MANAGER ============= 

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))

# =========================================     
    
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

# ============= FUNÇÕES AUXILIARES =============
def gerar_qr_code(equipamento_id):
    """Gera QR Code para o equipamento"""
    import qrcode
    from io import BytesIO
    import base64
    
    # Dados do QR Code
    qr_data = {
        'id': equipamento_id,
        'url': f"{request.host_url}equipamento/{equipamento_id}",
        'timestamp': datetime.now().isoformat()
    }
    
    # Gerar QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(str(qr_data))
    qr.make(fit=True)
    
    # Converter para base64
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_code_b64 = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{qr_code_b64}"

def registrar_historico(equipamento_id, acao, descricao, campo_alterado=None, valor_anterior=None, valor_novo=None, usuario_id=None):
    """Registra uma ação no histórico do equipamento"""
    try:
        historico = HistoricoEquipamento(
            equipamento_id=equipamento_id,
            acao=acao,
            descricao=descricao,
            campo_alterado=campo_alterado,
            valor_anterior=str(valor_anterior) if valor_anterior else None,
            valor_novo=str(valor_novo) if valor_novo else None,
            usuario_id=usuario_id or (current_user.id if current_user.is_authenticated else None),
            ip_address=request.remote_addr if request else None
        )
        db.session.add(historico)
        db.session.commit()
    except Exception as e:
        print(f"Erro ao registrar histórico: {e}")
        db.session.rollback()

def criar_notificacao(usuario_id, titulo, mensagem, tipo='info', equipamento_id=None, link_acao=None):
    """Cria uma notificação para o usuário"""
    try:
        notificacao = Notificacao(
            usuario_id=usuario_id,
            titulo=titulo,
            mensagem=mensagem,
            tipo=tipo,
            equipamento_id=equipamento_id,
            link_acao=link_acao
        )
        db.session.add(notificacao)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Erro ao criar notificação: {e}")
        db.session.rollback()
        return False

def verificar_garantias_expirando():
    """Verifica equipamentos com garantia expirando em 30 dias e cria notificações"""
    from datetime import timedelta
    
    data_limite = datetime.now().date() + timedelta(days=30)
    equipamentos_expirando = Equipamento.query.filter(
        Equipamento.garantia_ate <= data_limite,
        Equipamento.garantia_ate >= datetime.now().date(),
        Equipamento.ativo == True
    ).all()
    
    for equipamento in equipamentos_expirando:
        dias_restantes = (equipamento.garantia_ate - datetime.now().date()).days
        
        # Notificar usuários admin
        admins = Usuario.query.filter(Usuario.nivel_acesso >= 2, Usuario.ativo == True).all()
        for admin in admins:
            titulo = f"Garantia Expirando - {equipamento.id_publico}"
            mensagem = f"A garantia do equipamento {equipamento.tipo} ({equipamento.marca}) expira em {dias_restantes} dias."
            criar_notificacao(
                usuario_id=admin.id,
                titulo=titulo,
                mensagem=mensagem,
                tipo='warning',
                equipamento_id=equipamento.id_interno,
                link_acao=f"/consulta?busca={equipamento.id_publico}"
            )

def inicializar_dados_padrao():
    """Inicializa categorias e fornecedores padrão"""
    categorias_padrao = [
        {'nome': 'Hardware', 'icone': '💻', 'cor': '#3B82F6', 'descricao': 'Equipamentos de informática'},
        {'nome': 'Periféricos', 'icone': '🖱️', 'cor': '#10B981', 'descricao': 'Dispositivos periféricos'},
        {'nome': 'Mobiliário', 'icone': '🪑', 'cor': '#F59E0B', 'descricao': 'Móveis e mobiliário'},
        {'nome': 'Segurança', 'icone': '🔒', 'cor': '#EF4444', 'descricao': 'Equipamentos de segurança'},
        {'nome': 'Eletrônicos', 'icone': '📱', 'cor': '#8B5CF6', 'descricao': 'Dispositivos eletrônicos'},
        {'nome': 'Rede', 'icone': '🌐', 'cor': '#06B6D4', 'descricao': 'Equipamentos de rede'}
    ]
    
    for cat_data in categorias_padrao:
        if not Categoria.query.filter_by(nome=cat_data['nome']).first():
            categoria = Categoria(**cat_data)
            db.session.add(categoria)
    
    try:
        db.session.commit()
        print("Dados padrão inicializados com sucesso!")
    except Exception as e:
        print(f"Erro ao inicializar dados padrão: {e}")
        db.session.rollback()

# ============= ROTAS =============
@app.route('/index')
def index():
    return redirect(url_for('home'))


@app.route('/')
@login_required
def home():
    equipamentos = Equipamento.query.all()
    return render_template('dashboard.html', equipamentos=equipamentos)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(username=username).first()
        
        if usuario and bcrypt.checkpw(senha.encode('utf-8'), usuario.password_hash.encode('utf-8')):
            login_user(usuario)
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for('home'))
        flash("Credenciais inválidas!", "error")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout realizado com sucesso!", "success")
    return redirect(url_for('login'))

@app.route('/cadastro_usuario', methods=['GET', 'POST'])
@login_required
def cadastro_usuario():
    if request.method == 'POST':
        username = request.form['username'].strip()
        senha = request.form['senha'].strip()
        confirmar = request.form['confirmar'].strip()
        nivel = request.form.get('nivel', 1)
        
        if not username or not senha or not confirmar:
            flash("Preencha todos os campos!", "error")
            return redirect(url_for('cadastro_usuario'))
            
        if senha != confirmar:
            flash("Senhas não coincidem!", "error")
            return redirect(url_for('cadastro_usuario'))
            
        salt = bcrypt.gensalt()
        hash_senha = bcrypt.hashpw(senha.encode('utf-8'), salt)
        novo_usuario = Usuario(username=username, password_hash=hash_senha.decode('utf-8'), nivel_acesso=nivel)
        
        try:
            db.session.add(novo_usuario)
            db.session.commit()
            flash(f"Usuário {username} criado!", "success")
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash("Erro ao criar usuário!", "error")
            print(f"Erro: {e}")
    return render_template('cadastro_usuario.html')

@app.route('/uploads/images/<filename>')
def uploaded_image(filename):
    """Servir imagens uploadadas"""
    return send_file(os.path.join(app.config['IMAGES_FOLDER'], filename))

@app.route('/gerar_termo_cautela/<id_publico>')
@login_required
def gerar_termo_cautela(id_publico):
    """Gerar PDF do Termo de Cautela usando dados do equipamento"""
    try:
        # Buscar equipamento no banco
        equipamento = Equipamento.query.filter_by(id_publico=id_publico).first()
        if not equipamento:
            return jsonify({'error': 'Equipamento não encontrado'}), 404
        
        # Coletar dados do equipamento com tratamento seguro
        categoria_nome = 'N/A'
        if equipamento.categoria_id:
            categoria = Categoria.query.get(equipamento.categoria_id)
            categoria_nome = categoria.nome if categoria else 'N/A'
            
        fornecedor_nome = 'N/A'  
        if equipamento.fornecedor_id:
            fornecedor = Fornecedor.query.get(equipamento.fornecedor_id)
            fornecedor_nome = fornecedor.nome if fornecedor else 'N/A'
        
        dados = {
            'tipo': equipamento.tipo,
            'marca': equipamento.marca,
            'modelo': equipamento.modelo,
            'num_serie': equipamento.num_serie,
            'patrimonio': equipamento.id_publico,
            'valor': f"{equipamento.valor:.2f}" if equipamento.valor else '0,00',
            'responsavel': equipamento.responsavel or 'A definir',
            'localizacao': equipamento.localizacao,
            'observacoes': equipamento.observacoes or 'Nenhuma observação especial.',
            'categoria': categoria_nome,
            'fornecedor': fornecedor_nome,
            'codigo_barras': equipamento.codigo_barras or 'N/A',
            'data_emissao': datetime.now().strftime('%d/%m/%Y'),
            'usuario_emitente': current_user.nome_completo or 'Setor de TI/Patrimônio'
        }
        
        # Gerar PDF
        pdf_buffer = BytesIO()
        pdf = criar_termo_cautela_pdf(dados, pdf_buffer)
        pdf_buffer.seek(0)
        
        # Retornar PDF como download
        return Response(
            pdf_buffer.getvalue(),
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename=termo_cautela_{equipamento.id_publico}.pdf'}
        )
        
    except Exception as e:
        print(f"Erro ao gerar termo de cautela: {e}")
        return jsonify({'error': 'Erro ao gerar termo de cautela'}), 500

@app.route('/cadastrar', methods=['GET', 'POST'])
@login_required
def cadastrar():
    if request.method == 'POST':
        try:
            novo_id = 1
            ultimo = Equipamento.query.order_by(Equipamento.id_interno.desc()).first()
            if ultimo:
                novo_id = ultimo.id_interno + 1
            id_publico = f"PAT-{novo_id:03d}"
            nova_data_aquisicao = datetime.strptime(request.form['data_aquisicao'], '%Y-%m-%d')
            nova_ultima_manutencao = datetime.strptime(request.form['ultima_manutencao'], '%Y-%m-%d') if request.form['ultima_manutencao'] else None
            # Processar data de garantia
            nova_garantia_ate = None
            if request.form.get('garantia_ate'):
                nova_garantia_ate = datetime.strptime(request.form['garantia_ate'], '%Y-%m-%d').date()
                
            # Processar upload de imagem
            imagem_url = None
            if 'imagem' in request.files:
                file = request.files['imagem']
                if file and file.filename != '' and allowed_file(file.filename):
                    # Gerar nome único para o arquivo
                    filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                    filepath = os.path.join(app.config['IMAGES_FOLDER'], filename)
                    file.save(filepath)
                    imagem_url = f"/uploads/images/{filename}"
            
            # Gerar QR Code
            qr_code_data = f"PAT:{id_publico}|TIPO:{request.form['tipo']}|SERIE:{request.form['num_serie']}"
            
            novo_equipamento = Equipamento(
                id_publico=id_publico,
                tipo=request.form['tipo'],
                marca=request.form['marca'],
                modelo=request.form['modelo'],
                num_serie=request.form['num_serie'],
                data_aquisicao=nova_data_aquisicao,
                ultima_manutencao=nova_ultima_manutencao,
                localizacao=request.form['localizacao'],
                status=request.form['status'],
                responsavel=request.form['responsavel'],
                valor=float(request.form['valor']) if request.form['valor'] else 0.0,
                SPE=request.form['SPE'],
                observacoes=request.form['observacoes'],
                # Novos campos
                codigo_barras=request.form.get('codigo_barras') if request.form.get('codigo_barras') else None,
                garantia_ate=nova_garantia_ate,
                centro_custo=request.form.get('centro_custo'),
                fornecedor_id=int(request.form.get('fornecedor_id')) if request.form.get('fornecedor_id') else None,
                categoria_id=int(request.form.get('categoria_id')) if request.form.get('categoria_id') else None,
                vida_util_anos=int(request.form.get('vida_util_anos', 5)),
                # Campos modernizados
                imagem_url=imagem_url,
                qr_code=qr_code_data,
                ativo=True,
                # Auditoria
                created_by=current_user.id,
                updated_by=current_user.id
            )
            db.session.add(novo_equipamento)
            db.session.commit()
            flash(f"Equipamento {id_publico} cadastrado com sucesso!", "success")
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash("Erro ao cadastrar equipamento!", "error")
            print(f"Erro: {e}")
    
    # Buscar categorias e fornecedores para os selects
    categorias = Categoria.query.filter_by(ativo=True).order_by(Categoria.nome).all()
    fornecedores = Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome).all()
    
    return render_template('cadastro_equipamento.html', 
                         categorias=categorias, 
                         fornecedores=fornecedores)

@app.route('/consulta', methods=['GET', 'POST'])
@login_required
def consulta():
    busca = request.form.get('busca') if request.method == 'POST' else request.args.get('busca', '')
    ordenacao = request.args.get('ordenacao', 'id_publico')

    query = Equipamento.query
    if busca:
        query = query.filter(
            Equipamento.id_publico.ilike(f"%{busca}%") |
            Equipamento.tipo.ilike(f"%{busca}%") |
            Equipamento.marca.ilike(f"%{busca}%") |
            Equipamento.localizacao.ilike(f"%{busca}%")
        )

    if ordenacao == 'id_publico':
        query = query.order_by(Equipamento.id_publico.asc())  # ASC = crescente

    resultados = query.all()
    return render_template('consulta.html', resultados=resultados, busca=busca)



@app.route('/exportar_csv')
@login_required
def exportar_csv():
    try:
        equipamentos = Equipamento.query.all()
        df = pd.DataFrame([{
            'ID Público': e.id_publico,
            'Tipo': e.tipo,
            'Marca': e.marca,
            'Modelo': e.modelo,
            'Número Série': e.num_serie,
            'Data Aquisição': e.data_aquisicao,
            'Localização': e.localizacao,
            'Status': e.status,
            'Responsável': e.responsavel,
            'Valor': e.valor,
            'SPE': e.SPE
        } for e in equipamentos])
        
        csv_path = os.path.join(app.config['UPLOAD_FOLDER'], 'export.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        return send_file(csv_path, as_attachment=True)
    except Exception as e:
        flash("Erro ao exportar CSV!", "error")
        print(f"Erro: {e}")
        return redirect(url_for('home'))

@app.route('/gerar_pdf')
@login_required
def gerar_pdf():
    try:
        equipamentos = Equipamento.query.all()
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'inventario.pdf')
        
        doc = SimpleDocTemplate(pdf_path, pagesize=landscape(A4))
        elementos = []
        estilos = getSampleStyleSheet()
        
        # Cabeçalho
        titulo = Paragraph("Relatório de Inventário", estilos['Title'])
        elementos.append(titulo)
        elementos.append(Spacer(1, 12))
        
        # Tabela
        dados = [['ID', 'Tipo', 'Localização', 'Responsável', 'Status']]
        for e in equipamentos:
            dados.append([
                e.id_publico,
                e.tipo,
                e.localizacao,
                e.responsavel,
                e.status
            ])
            
        tabela = Table(dados, colWidths=[100, 150, 150, 150, 100])
        estilo = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ])
        tabela.setStyle(estilo)
        elementos.append(tabela)
        
        doc.build(elementos)
        return send_file(pdf_path, as_attachment=True)
    except Exception as e:
        flash("Erro ao gerar PDF!", "error")
        print(f"Erro: {e}")
        return redirect(url_for('home'))

@app.route('/upload_termo/<string:id_publico>', methods=['GET', 'POST'])
@login_required
def upload_termo(id_publico):
    equipamento = Equipamento.query.filter_by(id_publico=id_publico).first()

    if request.method == 'POST':
        try:
            if 'termo_pdf' not in request.files:
                flash("Nenhum arquivo foi enviado!", "error")
                return redirect(request.url)

            arquivo = request.files['termo_pdf']
            if not arquivo or arquivo.filename == '':
                flash("Arquivo inválido!", "error")
                return redirect(request.url)

            if allowed_file(arquivo.filename):
                if equipamento:
                    filename = f"{id_publico}.pdf"
                    
                    if USE_LOCAL_STORAGE:
                        # Salvar localmente
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        arquivo.save(filepath)
                        equipamento.termo_pdf_path = filename
                    else:
                        # Salvar no Azure
                        blob_client = container_client.get_blob_client(filename)
                        blob_client.upload_blob(arquivo, overwrite=True)
                        equipamento.termo_pdf_path = filename
                        
                    db.session.commit()
                    flash("Termo salvo com sucesso!", "success")
                    return redirect(url_for('consulta'))
                else:
                    flash("Equipamento não encontrado!", "error")
            else:
                flash("Somente arquivos PDF são permitidos!", "error")
        except Exception as e:
            flash(f"Erro inesperado ao salvar termo: {str(e)}", "error")
            print(f"Erro no upload: {e}")
            return redirect(request.url)

    termo_existe = bool(equipamento and equipamento.termo_pdf_path)
    return render_template('upload_termo.html', id_publico=id_publico, termo_existe=termo_existe)



@app.route('/ver_termo/<string:id_publico>')
@login_required
def ver_termo(id_publico):
    equipamento = Equipamento.query.filter_by(id_publico=id_publico).first()
    if equipamento and equipamento.termo_pdf_path:
        try:
            if USE_LOCAL_STORAGE:
                # Servir arquivo local
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], equipamento.termo_pdf_path)
                if os.path.exists(filepath):
                    return send_file(filepath, download_name=equipamento.termo_pdf_path, mimetype='application/pdf')
                else:
                    flash("Arquivo do termo não encontrado!", "error")
            else:
                # Servir do Azure
                blob_client = container_client.get_blob_client(equipamento.termo_pdf_path)
                stream = blob_client.download_blob().readall()
                return send_file(BytesIO(stream), download_name=equipamento.termo_pdf_path, mimetype='application/pdf')
        except Exception as e:
            flash(f"Erro ao acessar termo: {str(e)}", "error")
    else:
        flash("Termo não disponível para este equipamento.", "error")
    return redirect(url_for('consulta'))


@app.route('/solicitar_acesso', methods=['GET', 'POST'])
def solicitar_acesso():
    if request.method == 'POST':
        nome = request.form['nome']
        departamento = request.form['departamento']
        email = request.form['email']
        
        if enviar_email_solicitacao(nome, departamento, email):
            flash("Solicitação enviada para análise!", "success")
        else:
            flash("Erro ao enviar solicitação!", "error")
        return redirect(url_for('login'))
    return render_template('solicitar_acesso.html')

# ============= FUNÇÕES AUXILIARES =============
def enviar_email_solicitacao(nome, departamento, email_usuario):
    try:
        remetente = os.environ.get('EMAIL_USER')  # seu endereço Gmail
        senha = os.environ.get('EMAIL_PASSWORD')  # senha do app (não a sua senha normal)

        msg = MIMEMultipart()
        msg['From'] = remetente
        msg['To'] = remetente  # enviar para si mesmo ou para o admin
        msg['Subject'] = "Nova Solicitação de Acesso"

        corpo = f"""
        Nova solicitação de acesso:
        Nome: {nome}
        Departamento: {departamento}
        E-mail: {email_usuario}
        """
        msg.attach(MIMEText(corpo, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(remetente, senha)
            server.sendmail(remetente, remetente, msg.as_string())

        return True
    except Exception as e:
        print(f"Erro no envio de e-mail: {e}")
        return False

@app.context_processor
def inject_now():
    return {'datetime': datetime}

def criar_termo_cautela_pdf(dados, pdf_buffer):
    """Criar PDF do Termo de Cautela"""
    
    # Configurar documento
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Estilo customizado
    titulo_style = ParagraphStyle(
        'TituloTermo',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.darkgreen,
        alignment=1,  # Centralizado
        spaceAfter=20
    )
    
    subtitulo_style = ParagraphStyle(
        'SubtituloTermo',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.black,
        alignment=1,
        spaceAfter=15
    )
    
    normal_style = ParagraphStyle(
        'NormalTermo',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.black,
        spaceBefore=5,
        spaceAfter=5
    )
    
    # Conteúdo do PDF
    story = []
    
    # Cabeçalho
    story.append(Paragraph("TERMO DE CAUTELA DE EQUIPAMENTO", titulo_style))
    story.append(Paragraph("SISTEMA DE CONTROLE PATRIMONIAL", subtitulo_style))
    story.append(Spacer(1, 20))
    
    # Dados do equipamento em tabela
    equipamento_data = [
        ['DADOS DO EQUIPAMENTO', ''],
        ['Patrimônio:', dados.get('patrimonio', 'N/A')],
        ['Tipo:', dados.get('tipo', 'N/A')],
        ['Categoria:', dados.get('categoria', 'N/A')],
        ['Marca:', dados.get('marca', 'N/A')],
        ['Modelo:', dados.get('modelo', 'N/A')],
        ['Número de Série:', dados.get('num_serie', 'N/A')],
        ['Código de Barras:', dados.get('codigo_barras', 'N/A')],
        ['Valor:', f"R$ {dados.get('valor', '0,00')}"],
        ['Fornecedor:', dados.get('fornecedor', 'N/A')],
        ['Localização:', dados.get('localizacao', 'N/A')],
    ]
    
    equipamento_table = Table(equipamento_data, colWidths=[4*72, 4*72])
    equipamento_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(equipamento_table)
    story.append(Spacer(1, 20))
    
    # Responsabilidade
    story.append(Paragraph("TERMO DE RESPONSABILIDADE", subtitulo_style))
    
    texto_responsabilidade = f"""
    Eu, <b>{dados.get('responsavel', '__________________')}</b>, declaro ter recebido em perfeitas 
    condições o equipamento acima descrito, comprometendo-me a:
    
    • Utilizar o equipamento exclusivamente para fins profissionais;
    • Zelar pela conservação e guarda do equipamento;
    • Comunicar imediatamente qualquer problema, dano ou furto;
    • Devolver o equipamento quando solicitado pela empresa;
    • Responsabilizar-me por eventuais danos causados por mau uso.
    
    <b>Observações:</b> {dados.get('observacoes', 'Nenhuma observação especial.')}
    """
    
    story.append(Paragraph(texto_responsabilidade, normal_style))
    story.append(Spacer(1, 30))
    
    # QR Code (simulado como texto)
    qr_text = f"QR: PAT-{dados.get('patrimonio', 'XXX')} | {dados.get('tipo', 'N/A')}"
    story.append(Paragraph(f"<b>Código QR:</b> {qr_text}", normal_style))
    story.append(Spacer(1, 30))
    
    # Assinaturas
    assinatura_data = [
        ['ASSINATURAS', '', ''],
        ['', '', ''],
        ['_' * 30, '_' * 30, '_' * 30],
        ['Responsável pelo Equipamento', 'Setor de TI/Patrimônio', 'Data'],
        [dados.get('responsavel', ''), dados.get('usuario_emitente', ''), dados.get('data_emissao', '')]
    ]
    
    assinatura_table = Table(assinatura_data, colWidths=[2.5*72, 2.5*72, 1.5*72])
    assinatura_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 3), (-1, 3), 10),
    ]))
    
    story.append(assinatura_table)
    story.append(Spacer(1, 20))
    
    # Rodapé
    story.append(Paragraph(f"<i>Documento gerado automaticamente em {dados.get('data_emissao', 'N/A')} pelo Sistema de Controle Patrimonial.</i>", 
                          ParagraphStyle('Rodape', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=1)))
    
    # Construir PDF
    doc.build(story)
    return doc

# ============= INICIALIZAÇÃO DO BANCO =============
with app.app_context():
    db.create_all()

# ============= EXECUÇÃO DO SERVIDOR =============
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
