import os
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
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
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configuração do Azure Blob Storage
BLOB_CONTAINER = 'termos'
blob_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

if not blob_connection_string:
    raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING não definida!")

blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
container_client = blob_service_client.get_container_client(BLOB_CONTAINER)
try:
    container_client.create_container()
except Exception:
    pass  # container já existe


db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "error"

# ============= MODELOS =============
class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    nivel_acesso = db.Column(db.Integer, default=1)

class Equipamento(db.Model):
    id_interno = db.Column(db.Integer, primary_key=True)
    id_publico = db.Column(db.String(20), unique=True)
    tipo = db.Column(db.String(100))
    marca = db.Column(db.String(100))
    modelo = db.Column(db.String(100))
    num_serie = db.Column(db.String(100))
    data_aquisicao = db.Column(db.Date)
    localizacao = db.Column(db.String(200))
    status = db.Column(db.String(50))
    responsavel = db.Column(db.String(100))
    ultima_manutencao = db.Column(db.Date)
    valor = db.Column(db.Float)
    observacoes = db.Column(db.Text)
    SPE = db.Column(db.String(50))
    termo_pdf_path = db.Column(db.String(500))

# ============= CONFIGURAÇÕES =============
@app.before_request
def criar_admin_uma_vez():
    if not hasattr(app, 'admin_criado'):
        if not Usuario.query.filter_by(username='admin').first():
            hash_senha = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            admin = Usuario(username='admin', password_hash=hash_senha, nivel_acesso=3)
            db.session.add(admin)
            db.session.commit()
            print("Usuário admin criado: admin / admin123")
        app.admin_criado = True

# ============= LOGIN MANAGER ============= 

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# =========================================     
    
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

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
                observacoes=request.form['observacoes']
            )
            db.session.add(novo_equipamento)
            db.session.commit()
            flash(f"Equipamento {id_publico} cadastrado com sucesso!", "success")
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash("Erro ao cadastrar equipamento!", "error")
            print(f"Erro: {e}")
    return render_template('cadastro_equipamento.html')

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
            blob_client = container_client.get_blob_client(equipamento.termo_pdf_path)
            stream = blob_client.download_blob().readall()
            return send_file(BytesIO(stream), download_name=equipamento.termo_pdf_path, mimetype='application/pdf')
        except Exception:
            flash("Arquivo do termo não encontrado!", "error")
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

# ============= INICIALIZAÇÃO DO BANCO =============
with app.app_context():
    db.create_all()
