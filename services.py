"""
Serviços de negócio do Sistema de Controle de Patrimônio
Lógica de negócio separada das views
"""
import os
import qrcode
import base64
from io import BytesIO
from datetime import datetime, timedelta
from flask import request, current_app
from flask_login import current_user
from models import db, Equipamento, Categoria, Fornecedor, HistoricoEquipamento, Notificacao, Usuario

class EquipamentoService:
    """Serviços relacionados aos equipamentos"""
    
    @staticmethod
    def gerar_id_publico():
        """Gera um novo ID público para equipamento"""
        ultimo = Equipamento.query.order_by(Equipamento.id_interno.desc()).first()
        novo_id = 1 if not ultimo else ultimo.id_interno + 1
        return f"PAT-{novo_id:03d}"
    
    @staticmethod
    def gerar_qr_code(equipamento_id):
        """Gera QR Code para o equipamento"""
        qr_data = {
            'id': equipamento_id,
            'url': f"{request.host_url}equipamento/{equipamento_id}",
            'timestamp': datetime.now().isoformat()
        }
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(str(qr_data))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_b64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{qr_code_b64}"
    
    @staticmethod
    def criar_equipamento(dados_formulario):
        """Cria um novo equipamento com todos os dados"""
        try:
            id_publico = EquipamentoService.gerar_id_publico()
            
            # Processar datas
            data_aquisicao = None
            if dados_formulario.get('data_aquisicao'):
                data_aquisicao = datetime.strptime(dados_formulario['data_aquisicao'], '%Y-%m-%d').date()
            
            ultima_manutencao = None
            if dados_formulario.get('ultima_manutencao'):
                ultima_manutencao = datetime.strptime(dados_formulario['ultima_manutencao'], '%Y-%m-%d').date()
            
            garantia_ate = None
            if dados_formulario.get('garantia_ate'):
                garantia_ate = datetime.strptime(dados_formulario['garantia_ate'], '%Y-%m-%d').date()
            
            # Gerar QR Code
            qr_code_data = f"PAT:{id_publico}|TIPO:{dados_formulario['tipo']}|SERIE:{dados_formulario['num_serie']}"
            
            equipamento = Equipamento(
                id_publico=id_publico,
                tipo=dados_formulario['tipo'],
                marca=dados_formulario['marca'],
                modelo=dados_formulario['modelo'],
                num_serie=dados_formulario['num_serie'],
                data_aquisicao=data_aquisicao,
                ultima_manutencao=ultima_manutencao,
                localizacao=dados_formulario['localizacao'],
                status=dados_formulario['status'],
                responsavel=dados_formulario.get('responsavel', ''),
                valor=float(dados_formulario['valor']) if dados_formulario.get('valor') else 0.0,
                SPE=dados_formulario.get('SPE', ''),
                observacoes=dados_formulario.get('observacoes', ''),
                codigo_barras=dados_formulario.get('codigo_barras') or None,
                garantia_ate=garantia_ate,
                centro_custo=dados_formulario.get('centro_custo'),
                fornecedor_id=int(dados_formulario['fornecedor_id']) if dados_formulario.get('fornecedor_id') else None,
                categoria_id=int(dados_formulario['categoria_id']) if dados_formulario.get('categoria_id') else None,
                vida_util_anos=int(dados_formulario.get('vida_util_anos', 5)),
                qr_code=qr_code_data,
                ativo=True,
                created_by=current_user.id if current_user.is_authenticated else None,
                updated_by=current_user.id if current_user.is_authenticated else None
            )
            
            db.session.add(equipamento)
            db.session.commit()
            
            # Registrar no histórico
            HistoricoService.registrar_acao(
                equipamento.id_interno,
                'Criado',
                f'Equipamento {id_publico} criado no sistema'
            )
            
            return equipamento, None
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)

class HistoricoService:
    """Serviços relacionados ao histórico"""
    
    @staticmethod
    def registrar_acao(equipamento_id, acao, descricao, campo_alterado=None, valor_anterior=None, valor_novo=None):
        """Registra uma ação no histórico do equipamento"""
        try:
            historico = HistoricoEquipamento(
                equipamento_id=equipamento_id,
                acao=acao,
                descricao=descricao,
                campo_alterado=campo_alterado,
                valor_anterior=str(valor_anterior) if valor_anterior else None,
                valor_novo=str(valor_novo) if valor_novo else None,
                usuario_id=current_user.id if current_user.is_authenticated else None,
                ip_address=request.remote_addr if request else None
            )
            db.session.add(historico)
            db.session.commit()
            return True
        except Exception as e:
            current_app.logger.error(f"Erro ao registrar histórico: {e}")
            db.session.rollback()
            return False

class NotificacaoService:
    """Serviços relacionados às notificações"""
    
    @staticmethod
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
            current_app.logger.error(f"Erro ao criar notificação: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def verificar_garantias_expirando():
        """Verifica equipamentos com garantia expirando em 30 dias e cria notificações"""
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
                NotificacaoService.criar_notificacao(
                    usuario_id=admin.id,
                    titulo=titulo,
                    mensagem=mensagem,
                    tipo='warning',
                    equipamento_id=equipamento.id_interno,
                    link_acao=f"/consulta?busca={equipamento.id_publico}"
                )

class ReportService:
    """Serviços relacionados aos relatórios"""
    
    @staticmethod
    def gerar_dados_dashboard():
        """Gera dados para o dashboard"""
        try:
            total = Equipamento.query.count()
            em_uso = Equipamento.query.filter_by(status='Em uso').count()
            manutencao = Equipamento.query.filter_by(status='Manutenção').count()
            estocado = Equipamento.query.filter_by(status='Estocado').count()
            
            valor_total = db.session.query(db.func.sum(Equipamento.valor)).scalar() or 0
            
            return {
                'total': total,
                'em_uso': em_uso,
                'manutencao': manutencao,
                'estocado': estocado,
                'valor_total': float(valor_total)
            }
        except Exception as e:
            current_app.logger.error(f"Erro ao gerar dados do dashboard: {e}")
            return None

class SearchService:
    """Serviços relacionados à busca"""
    
    @staticmethod
    def buscar_equipamentos(query, limit=10):
        """Busca equipamentos por texto"""
        if len(query) < 2:
            return []
        
        try:
            equipamentos = Equipamento.query.filter(
                db.or_(
                    Equipamento.id_publico.ilike(f'%{query}%'),
                    Equipamento.tipo.ilike(f'%{query}%'),
                    Equipamento.marca.ilike(f'%{query}%'),
                    Equipamento.responsavel.ilike(f'%{query}%')
                )
            ).limit(limit).all()
            
            return [eq.to_dict() for eq in equipamentos]
        except Exception as e:
            current_app.logger.error(f"Erro na busca: {e}")
            return []

class InitService:
    """Serviços relacionados à inicialização"""
    
    @staticmethod
    def inicializar_dados_padrao():
        """Inicializa categorias e fornecedores padrão"""
        try:
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
            
            db.session.commit()
            return True
        except Exception as e:
            current_app.logger.error(f"Erro ao inicializar dados: {e}")
            db.session.rollback()
            return False