"""
Views/Controllers do Sistema de Controle de Patrimônio
Separação das rotas e lógica de apresentação
"""
import os
import pandas as pd
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, send_file, jsonify, Response, session
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.utils import secure_filename
import uuid
import bcrypt

from models import db, Usuario, Equipamento, Categoria, Fornecedor
from services import EquipamentoService, HistoricoService, ReportService, SearchService
from utils import criar_termo_cautela_pdf, allowed_file

def init_routes(app):
    """Inicializa todas as rotas da aplicação"""
    
    @app.route('/')
    @login_required
    def home():
        """Página inicial - Dashboard"""
        return render_template('dashboard.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Página de login"""
        if request.method == 'POST':
            username = request.form['username']
            senha = request.form['senha']
            usuario = Usuario.query.filter_by(username=username, ativo=True).first()
            
            if usuario and bcrypt.checkpw(senha.encode('utf-8'), usuario.password_hash.encode('utf-8')):
                login_user(usuario)
                
                # Configurar sessão para compatibilidade
                session['username'] = usuario.username
                session['nivel_acesso'] = usuario.nivel_acesso
                session['usuario_id'] = usuario.id
                
                # Atualizar último login
                usuario.last_login = datetime.utcnow()
                db.session.commit()
                
                flash("Login realizado com sucesso!", "success")
                return redirect(url_for('home'))
            flash("Credenciais inválidas ou usuário inativo!", "error")
        return render_template('login.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        """Logout do usuário"""
        logout_user()
        
        # Limpar sessão
        session.clear()
        
        flash("Logout realizado com sucesso!", "success")
        return redirect(url_for('login'))
    
    @app.route('/cadastro_usuario', methods=['GET', 'POST'])
    @login_required
    def cadastro_usuario():
        """Cadastro de novo usuário"""
        # Verificar se usuário tem permissão (nível 3 = admin)
        if current_user.nivel_acesso < 3:
            flash("Você não tem permissão para cadastrar usuários!", "error")
            return redirect(url_for('home'))
        
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
                
            # Verificar se usuário já existe
            if Usuario.query.filter_by(username=username).first():
                flash("Nome de usuário já existe!", "error")
                return redirect(url_for('cadastro_usuario'))
            
            try:
                salt = bcrypt.gensalt()
                hash_senha = bcrypt.hashpw(senha.encode('utf-8'), salt)
                novo_usuario = Usuario(
                    username=username, 
                    password_hash=hash_senha.decode('utf-8'), 
                    nivel_acesso=nivel,
                    ativo=True,
                    created_at=datetime.utcnow()
                )
                
                db.session.add(novo_usuario)
                db.session.commit()
                flash(f"Usuário {username} criado com sucesso!", "success")
                return redirect(url_for('home'))
            except Exception as e:
                db.session.rollback()
                flash("Erro ao criar usuário!", "error")
                app.logger.error(f"Erro ao criar usuário: {e}")
                
        return render_template('cadastro_usuario.html')
    
    @app.route('/solicitar_acesso', methods=['GET', 'POST'])
    def solicitar_acesso():
        """Página para solicitar acesso ao administrador"""
        if request.method == 'POST':
            nome = request.form.get('nome')
            email = request.form.get('email')
            justificativa = request.form.get('justificativa')
            
            # Por enquanto, apenas mostra mensagem de sucesso
            # Em produção, enviaria email ou criaria ticket
            flash(f"Solicitação de acesso para {nome} enviada ao administrador!", "info")
            return redirect(url_for('login'))
        
        return render_template('solicitar_acesso.html')
    
    @app.route('/cadastrar', methods=['GET', 'POST'])
    @login_required
    def cadastrar():
        """Cadastro de equipamento"""
        if request.method == 'POST':
            try:
                # Processar upload de imagem
                imagem_url = None
                if 'imagem' in request.files:
                    file = request.files['imagem']
                    if file and file.filename != '' and allowed_file(file.filename):
                        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                        filepath = os.path.join(app.config['IMAGES_FOLDER'], filename)
                        file.save(filepath)
                        imagem_url = f"/uploads/images/{filename}"
                
                equipamento, erro = EquipamentoService.criar_equipamento(request.form.to_dict())
                
                if equipamento:
                    if imagem_url:
                        equipamento.imagem_url = imagem_url
                        db.session.commit()
                    
                    flash(f"Equipamento {equipamento.id_publico} cadastrado com sucesso!", "success")
                    return redirect(url_for('home'))
                else:
                    flash(f"Erro ao cadastrar equipamento: {erro}", "error")
                    
            except Exception as e:
                db.session.rollback()
                flash("Erro inesperado ao cadastrar equipamento!", "error")
                app.logger.error(f"Erro no cadastro: {e}")
        
        # Buscar categorias e fornecedores para os selects
        categorias = Categoria.query.filter_by(ativo=True).order_by(Categoria.nome).all()
        fornecedores = Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome).all()
        
        return render_template('cadastro_equipamento.html', 
                             categorias=categorias, 
                             fornecedores=fornecedores)
    
    # ============= API ENDPOINTS PARA MODAIS =============
    
    @app.route('/api/fornecedor/criar', methods=['POST'])
    @login_required
    def api_criar_fornecedor():
        """API para criar fornecedor via modal"""
        try:
            data = request.get_json()
            nome = data.get('nome', '').strip()
            
            if not nome:
                return jsonify({'success': False, 'error': 'Nome é obrigatório'}), 400
            
            # Verificar se já existe
            existe = Fornecedor.query.filter_by(nome=nome).first()
            if existe:
                return jsonify({'success': False, 'error': 'Fornecedor já existe'}), 400
            
            # Criar novo fornecedor
            fornecedor = Fornecedor(
                nome=nome,
                cnpj=data.get('cnpj', '').strip() or None,
                telefone=data.get('telefone', '').strip() or None,
                ativo=True
            )
            
            db.session.add(fornecedor)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'id': fornecedor.id,
                'nome': fornecedor.nome
            })
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Erro ao criar fornecedor: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/categoria/criar', methods=['POST'])
    @login_required
    def api_criar_categoria():
        """API para criar categoria via modal"""
        try:
            data = request.get_json()
            nome = data.get('nome', '').strip()
            
            if not nome:
                return jsonify({'success': False, 'error': 'Nome é obrigatório'}), 400
            
            # Verificar se já existe
            existe = Categoria.query.filter_by(nome=nome).first()
            if existe:
                return jsonify({'success': False, 'error': 'Categoria já existe'}), 400
            
            # Criar nova categoria
            categoria = Categoria(
                nome=nome,
                descricao=data.get('descricao', '').strip() or None,
                ativo=True
            )
            
            db.session.add(categoria)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'id': categoria.id,
                'nome': categoria.nome
            })
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Erro ao criar categoria: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/consulta', methods=['GET', 'POST'])
    @login_required
    def consulta():
        """Consulta de equipamentos"""
        busca = request.form.get('busca') if request.method == 'POST' else request.args.get('busca', '')
        ordenacao = request.args.get('ordenacao', 'id_publico')

        query = Equipamento.query
        if busca:
            query = query.filter(
                db.or_(
                    Equipamento.id_publico.ilike(f"%{busca}%"),
                    Equipamento.tipo.ilike(f"%{busca}%"),
                    Equipamento.marca.ilike(f"%{busca}%"),
                    Equipamento.localizacao.ilike(f"%{busca}%"),
                    Equipamento.responsavel.ilike(f"%{busca}%")
                )
            )

        if ordenacao == 'id_publico':
            query = query.order_by(Equipamento.id_publico.asc())

        resultados = query.all()
        return render_template('consulta.html', resultados=resultados, busca=busca)
    
    @app.route('/equipamento/<id_publico>/editar', methods=['GET', 'POST'])
    @login_required
    def editar_equipamento(id_publico):
        """Editar equipamento"""
        equipamento = Equipamento.query.filter_by(id_publico=id_publico).first_or_404()
        
        # Verificar permissão (nível 2 ou 3 podem editar)
        if current_user.nivel_acesso < 2:
            flash('Você não tem permissão para editar equipamentos!', 'error')
            return redirect(url_for('consulta'))
        
        if request.method == 'POST':
            try:
                # Armazenar valores antigos para histórico
                campos_alterados = []
                
                # Atualizar campos básicos
                campos_basicos = {
                    'tipo': request.form.get('tipo'),
                    'marca': request.form.get('marca'),
                    'modelo': request.form.get('modelo'),
                    'num_serie': request.form.get('num_serie'),
                    'localizacao': request.form.get('localizacao'),
                    'status': request.form.get('status'),
                    'responsavel': request.form.get('responsavel'),
                    'SPE': request.form.get('SPE'),
                    'observacoes': request.form.get('observacoes')
                }
                
                for campo, valor_novo in campos_basicos.items():
                    valor_antigo = getattr(equipamento, campo)
                    if valor_novo and str(valor_antigo) != str(valor_novo):
                        campos_alterados.append({
                            'campo': campo,
                            'antigo': valor_antigo,
                            'novo': valor_novo
                        })
                        setattr(equipamento, campo, valor_novo)
                
                # Campos numéricos
                if request.form.get('valor'):
                    valor_novo = float(request.form.get('valor'))
                    if equipamento.valor != valor_novo:
                        campos_alterados.append({
                            'campo': 'valor',
                            'antigo': equipamento.valor,
                            'novo': valor_novo
                        })
                        equipamento.valor = valor_novo
                
                # Campos de data
                if request.form.get('data_aquisicao'):
                    data_nova = datetime.strptime(request.form.get('data_aquisicao'), '%Y-%m-%d').date()
                    if equipamento.data_aquisicao != data_nova:
                        campos_alterados.append({
                            'campo': 'data_aquisicao',
                            'antigo': equipamento.data_aquisicao,
                            'novo': data_nova
                        })
                        equipamento.data_aquisicao = data_nova
                
                if request.form.get('ultima_manutencao'):
                    data_nova = datetime.strptime(request.form.get('ultima_manutencao'), '%Y-%m-%d').date()
                    if equipamento.ultima_manutencao != data_nova:
                        campos_alterados.append({
                            'campo': 'ultima_manutencao',
                            'antigo': equipamento.ultima_manutencao,
                            'novo': data_nova
                        })
                        equipamento.ultima_manutencao = data_nova
                
                # Atualizar auditoria
                equipamento.updated_at = datetime.utcnow()
                equipamento.updated_by = current_user.id
                
                # Upload de imagem (se houver)
                if 'imagem' in request.files:
                    file = request.files['imagem']
                    if file and file.filename != '' and allowed_file(file.filename):
                        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                        filepath = os.path.join(app.config['IMAGES_FOLDER'], filename)
                        file.save(filepath)
                        equipamento.imagem_url = f"/uploads/images/{filename}"
                        campos_alterados.append({
                            'campo': 'imagem_url',
                            'antigo': 'sem imagem',
                            'novo': 'imagem atualizada'
                        })
                
                db.session.commit()
                
                # Registrar histórico para cada campo alterado
                for alteracao in campos_alterados:
                    HistoricoService.registrar_acao(
                        equipamento_id=equipamento.id_interno,
                        acao='Editado',
                        campo_alterado=alteracao['campo'],
                        valor_anterior=str(alteracao['antigo']),
                        valor_novo=str(alteracao['novo']),
                        descricao=f"Campo '{alteracao['campo']}' alterado de '{alteracao['antigo']}' para '{alteracao['novo']}'"
                    )
                
                flash(f'Equipamento {equipamento.id_publico} atualizado com sucesso!', 'success')
                return redirect(url_for('consulta'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Erro ao atualizar equipamento: {str(e)}', 'error')
                app.logger.error(f"Erro ao editar equipamento: {e}")
        
        # GET - Buscar dados para os selects
        categorias = Categoria.query.filter_by(ativo=True).order_by(Categoria.nome).all()
        fornecedores = Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome).all()
        
        return render_template('editar_equipamento.html', 
                             equipamento=equipamento,
                             categorias=categorias,
                             fornecedores=fornecedores)
    
    @app.route('/equipamento/<id_publico>/excluir', methods=['POST'])
    @login_required
    def excluir_equipamento(id_publico):
        """Excluir equipamento (apenas admin)"""
        if current_user.nivel_acesso < 3:
            flash('Apenas administradores podem excluir equipamentos!', 'error')
            return redirect(url_for('consulta'))
        
        equipamento = Equipamento.query.filter_by(id_publico=id_publico).first_or_404()
        
        try:
            # Registrar no histórico antes de excluir
            HistoricoService.registrar_acao(
                equipamento_id=equipamento.id_interno,
                acao='Excluído',
                descricao=f"Equipamento {equipamento.id_publico} ({equipamento.tipo}) excluído por {current_user.username}"
            )
            
            # Deletar
            db.session.delete(equipamento)
            db.session.commit()
            
            flash(f'Equipamento {id_publico} excluído com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao excluir equipamento: {str(e)}', 'error')
            app.logger.error(f"Erro ao excluir equipamento: {e}")
        
        return redirect(url_for('consulta'))
    
    @app.route('/exportar_csv')
    @login_required
    def exportar_csv():
        """Exportar dados para CSV"""
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
                'SPE': e.SPE,
                'Centro de Custo': e.centro_custo,
                'Garantia até': e.garantia_ate
            } for e in equipamentos])
            
            csv_path = os.path.join(app.config['UPLOAD_FOLDER'], 'export.csv')
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            return send_file(csv_path, as_attachment=True, download_name=f'equipamentos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        except Exception as e:
            flash("Erro ao exportar CSV!", "error")
            app.logger.error(f"Erro na exportação CSV: {e}")
            return redirect(url_for('home'))
    
    @app.route('/gerar_pdf')
    @login_required
    def gerar_pdf():
        """Gerar relatório PDF"""
        try:
            equipamentos = Equipamento.query.all()
            # Implementar geração de PDF aqui
            flash("Funcionalidade de PDF será implementada em breve!", "info")
            return redirect(url_for('home'))
        except Exception as e:
            flash("Erro ao gerar PDF!", "error")
            app.logger.error(f"Erro na geração PDF: {e}")
            return redirect(url_for('home'))
    
    # API Routes
    @app.route('/api/dashboard-stats')
    @login_required
    def api_dashboard_stats():
        """API: Estatísticas do dashboard"""
        try:
            stats = ReportService.gerar_dados_dashboard()
            if stats:
                return jsonify(stats)
            else:
                return jsonify({'error': 'Erro ao gerar estatísticas'}), 500
        except Exception as e:
            app.logger.error(f"Erro na API dashboard: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/search')
    @login_required
    def api_search():
        """API: Busca instantânea"""
        query = request.args.get('q', '')
        
        try:
            resultados = SearchService.buscar_equipamentos(query)
            return jsonify({'resultados': resultados})
        except Exception as e:
            app.logger.error(f"Erro na API de busca: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/gerar_termo_cautela/<id_publico>')
    @login_required
    def gerar_termo_cautela(id_publico):
        """Gerar PDF do Termo de Cautela"""
        try:
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
            from io import BytesIO
            pdf_buffer = BytesIO()
            criar_termo_cautela_pdf(dados, pdf_buffer)
            pdf_buffer.seek(0)
            
            # Registrar ação no histórico
            HistoricoService.registrar_acao(
                equipamento.id_interno,
                'Termo Gerado',
                f'Termo de cautela gerado por {current_user.username}'
            )
            
            return Response(
                pdf_buffer.getvalue(),
                mimetype='application/pdf',
                headers={'Content-Disposition': f'attachment; filename=termo_cautela_{equipamento.id_publico}.pdf'}
            )
            
        except Exception as e:
            app.logger.error(f"Erro ao gerar termo de cautela: {e}")
            return jsonify({'error': 'Erro ao gerar termo de cautela'}), 500
    
    @app.route('/upload_termo/<id_publico>', methods=['GET', 'POST'])
    @login_required
    def upload_termo(id_publico):
        """Upload de termo de cautela"""
        equipamento = Equipamento.query.filter_by(id_publico=id_publico).first_or_404()
        
        if request.method == 'POST':
            if 'termo' not in request.files:
                flash('Nenhum arquivo selecionado!', 'error')
                return redirect(request.url)
            
            file = request.files['termo']
            if file.filename == '':
                flash('Nenhum arquivo selecionado!', 'error')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                try:
                    filename = f"termo_{equipamento.id_publico}_{secure_filename(file.filename or 'termo.pdf')}"
                    upload_dir = os.path.join('uploads', 'termos')
                    os.makedirs(upload_dir, exist_ok=True)
                    filepath = os.path.join(upload_dir, filename)
                    file.save(filepath)
                    
                    # Atualizar equipamento com caminho do termo
                    equipamento.termo_pdf_path = filepath
                    db.session.commit()
                    
                    # Registrar histórico
                    HistoricoService.registrar_acao(
                        equipamento_id=equipamento.id,
                        campo_alterado='termo_pdf',
                        valor_anterior='Sem termo',
                        valor_novo=filename,
                        acao='Upload Termo',
                        descricao=f'Termo de cautela enviado por {current_user.username}'
                    )
                    
                    flash('Termo enviado com sucesso!', 'success')
                    return redirect(url_for('consulta'))
                    
                except Exception as e:
                    app.logger.error(f"Erro ao fazer upload do termo: {e}")
                    flash('Erro ao enviar termo!', 'error')
            else:
                flash('Tipo de arquivo não permitido!', 'error')
        
        return render_template('upload_termo.html', equipamento=equipamento)
    
    @app.route('/ver_termo/<id_publico>')
    @login_required
    def ver_termo(id_publico):
        """Visualizar termo de cautela"""
        import os
        equipamento = Equipamento.query.filter_by(id_publico=id_publico).first_or_404()
        
        if not equipamento.termo_pdf_path or equipamento.termo_pdf_path == 'None':
            flash('Termo não encontrado!', 'error')
            return redirect(url_for('consulta'))
        
        try:
            # Caminho relativo pode estar apenas com o nome do arquivo
            pdf_path = equipamento.termo_pdf_path
            
            # Se for apenas um nome de arquivo, procurar na pasta uploads
            if not os.path.isabs(pdf_path):
                # Tentar em uploads/termos/
                full_path = os.path.join(app.config.get('UPLOAD_FOLDER', 'uploads/termos'), os.path.basename(pdf_path))
                if os.path.exists(full_path):
                    pdf_path = full_path
                else:
                    # Tentar no diretório raiz (compatibilidade com versão anterior)
                    root_path = os.path.basename(pdf_path)
                    if os.path.exists(root_path):
                        pdf_path = root_path
                    else:
                        flash(f'Arquivo não encontrado: {equipamento.termo_pdf_path}', 'error')
                        return redirect(url_for('consulta'))
            
            if not os.path.exists(pdf_path):
                flash(f'Arquivo não encontrado: {pdf_path}', 'error')
                return redirect(url_for('consulta'))
            
            return send_file(
                pdf_path,
                as_attachment=False,
                mimetype='application/pdf'
            )
        except Exception as e:
            app.logger.error(f"Erro ao visualizar termo: {e}")
            flash('Erro ao visualizar termo!', 'error')
            return redirect(url_for('consulta'))
    
    # ============= GESTÃO DE USUÁRIOS (ADMIN) =============
    
    @app.route('/admin/usuarios')
    @login_required
    def admin_usuarios():
        """Página de gestão de usuários (apenas para admin)"""
        if current_user.nivel_acesso < 3:
            flash('Acesso negado! Apenas administradores.', 'error')
            return redirect(url_for('home'))
        
        usuarios = Usuario.query.all()
        return render_template('admin_usuarios.html', usuarios=usuarios)
    
    @app.route('/admin/usuario/<int:user_id>/editar', methods=['GET', 'POST'])
    @login_required
    def admin_editar_usuario(user_id):
        """Editar usuário (apenas para admin)"""
        if current_user.nivel_acesso < 3:
            flash('Acesso negado! Apenas administradores.', 'error')
            return redirect(url_for('home'))
        
        usuario = Usuario.query.get_or_404(user_id)
        
        if request.method == 'POST':
            try:
                # Atualizar dados básicos
                usuario.nome_completo = request.form.get('nome_completo', usuario.nome_completo)
                usuario.nivel_acesso = int(request.form.get('nivel_acesso', usuario.nivel_acesso))
                usuario.ativo = 'ativo' in request.form
                
                # Resetar senha se solicitado
                nova_senha = request.form.get('nova_senha')
                if nova_senha:
                    hash_senha = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    usuario.password_hash = hash_senha
                    flash(f'Senha do usuário {usuario.username} foi resetada!', 'warning')
                
                db.session.commit()
                
                # Registrar histórico da ação
                HistoricoService.registrar_acao(
                    equipamento_id=None,
                    acao='Usuário Editado',
                    descricao=f'Usuário {usuario.username} editado por {current_user.username}',
                    campo_alterado='user_management',
                    valor_anterior='',
                    valor_novo=f'Nível: {usuario.nivel_acesso}, Ativo: {usuario.ativo}'
                )
                
                flash(f'Usuário {usuario.username} atualizado com sucesso!', 'success')
                return redirect(url_for('admin_usuarios'))
                
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Erro ao editar usuário: {e}")
                flash('Erro ao atualizar usuário!', 'error')
        
        return render_template('admin_editar_usuario.html', usuario=usuario)
    
    @app.route('/admin/usuario/<int:user_id>/toggle_status', methods=['POST'])
    @login_required
    def admin_toggle_usuario_status(user_id):
        """Ativar/Desativar usuário"""
        if current_user.nivel_acesso < 3:
            return jsonify({'error': 'Acesso negado'}), 403
        
        usuario = Usuario.query.get_or_404(user_id)
        
        # Não permitir desativar a si mesmo
        if usuario.id == current_user.id:
            return jsonify({'error': 'Não é possível desativar sua própria conta'}), 400
        
        try:
            usuario.ativo = not usuario.ativo
            status_texto = 'ativado' if usuario.ativo else 'desativado'
            
            db.session.commit()
            
            # Registrar histórico
            HistoricoService.registrar_acao(
                equipamento_id=None,
                acao=f'Usuário {status_texto.title()}',
                descricao=f'Usuário {usuario.username} {status_texto} por {current_user.username}'
            )
            
            flash(f'Usuário {usuario.username} {status_texto} com sucesso!', 'success')
            return jsonify({'success': True, 'status': usuario.ativo})
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Erro ao alterar status do usuário: {e}")
            return jsonify({'error': 'Erro ao alterar status'}), 500
    
    @app.route('/admin/usuario/<int:user_id>/resetar_senha', methods=['POST'])
    @login_required
    def admin_resetar_senha(user_id):
        """Resetar senha do usuário para padrão"""
        if current_user.nivel_acesso < 3:
            return jsonify({'error': 'Acesso negado'}), 403
        
        usuario = Usuario.query.get_or_404(user_id)
        
        try:
            # Senha padrão: 123456
            nova_senha = '123456'
            hash_senha = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            usuario.password_hash = hash_senha
            
            db.session.commit()
            
            # Registrar histórico
            HistoricoService.registrar_acao(
                equipamento_id=None,
                acao='Senha Resetada',
                descricao=f'Senha do usuário {usuario.username} resetada por {current_user.username}'
            )
            
            return jsonify({
                'success': True, 
                'message': f'Senha do usuário {usuario.username} resetada para: {nova_senha}'
            })
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Erro ao resetar senha: {e}")
            return jsonify({'error': 'Erro ao resetar senha'}), 500
    
    @app.route('/admin/usuario/<int:user_id>/excluir', methods=['POST'])
    @login_required
    def admin_excluir_usuario(user_id):
        """Excluir usuário"""
        if current_user.nivel_acesso < 3:
            return jsonify({'error': 'Acesso negado'}), 403
        
        usuario = Usuario.query.get_or_404(user_id)
        
        # Não permitir excluir a si mesmo
        if usuario.id == current_user.id:
            return jsonify({'error': 'Não é possível excluir sua própria conta'}), 400
        
        # Não permitir excluir o admin padrão
        if usuario.username == 'admin':
            return jsonify({'error': 'Não é possível excluir o administrador padrão'}), 400
        
        try:
            username = usuario.username
            db.session.delete(usuario)
            db.session.commit()
            
            # Registrar histórico
            HistoricoService.registrar_acao(
                equipamento_id=None,
                acao='Usuário Excluído',
                descricao=f'Usuário {username} excluído por {current_user.username}'
            )
            
            return jsonify({'success': True, 'message': f'Usuário {username} excluído com sucesso'})
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Erro ao excluir usuário: {e}")
            return jsonify({'error': 'Erro ao excluir usuário'}), 500
    
    @app.route('/admin/relatorio_usuarios')
    @login_required
    def admin_relatorio_usuarios():
        """Relatório de usuários e atividades"""
        if current_user.nivel_acesso < 3:
            flash('Acesso negado! Apenas administradores.', 'error')
            return redirect(url_for('home'))
        
        # Estatísticas de usuários
        total_usuarios = Usuario.query.count()
        usuarios_ativos = Usuario.query.filter_by(ativo=True).count()
        usuarios_inativos = total_usuarios - usuarios_ativos
        
        # Usuários por nível de acesso
        nivel_1 = Usuario.query.filter_by(nivel_acesso=1).count()  # Visualizador
        nivel_2 = Usuario.query.filter_by(nivel_acesso=2).count()  # Operador
        nivel_3 = Usuario.query.filter_by(nivel_acesso=3).count()  # Admin
        
        dados = {
            'now': datetime.utcnow(),
            'usuarios': Usuario.query.order_by(Usuario.created_at.desc()).all(),
            'stats': {
                'total_usuarios': total_usuarios,
                'usuarios_ativos': usuarios_ativos,
                'usuarios_inativos': usuarios_inativos,
                'admins': nivel_3,
                'nivel_1': nivel_1,
                'nivel_2': nivel_2,
                'nivel_3': nivel_3
            }
        }
        
        return render_template('admin_relatorio_usuarios.html', **dados)