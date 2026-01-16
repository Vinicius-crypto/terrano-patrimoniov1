"""Adicionar campos modernos e tabelas novas preservando dados existentes

Revision ID: adicionar_campos_modernos
Revises: 
Create Date: 2026-01-16

IMPORTANTE: Esta migração PRESERVA todos os dados existentes!
- Adiciona 27 novos campos na tabela equipamento (todos nullable)
- Adiciona 6 novos campos na tabela usuario (todos nullable)
- Cria 5 tabelas novas (categoria, fornecedor, historico, notificacao, manutencao)
- NÃO remove ou modifica dados existentes
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = 'adicionar_campos_modernos'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Adicionar campos e tabelas novas"""
    
    print("🚀 Iniciando migração - Adicionando campos modernos...")
    
    # ==================================================
    # TABELA EQUIPAMENTO - Adicionar campos novos
    # ==================================================
    print("📊 Atualizando tabela EQUIPAMENTO...")
    
    with op.batch_alter_table('equipamento', schema=None) as batch_op:
        # Financeiros
        batch_op.add_column(sa.Column('valor_residual', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('vida_util_anos', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('valor_depreciado', sa.Float(), nullable=True))
        
        # Localização e Responsabilidade
        batch_op.add_column(sa.Column('centro_custo', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('departamento', sa.String(length=100), nullable=True))
        
        # Status e Manutenção
        batch_op.add_column(sa.Column('condicao', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('proxima_manutencao', sa.Date(), nullable=True))
        
        # Garantia e Fornecedor
        batch_op.add_column(sa.Column('garantia_ate', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('fornecedor_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('nota_fiscal', sa.String(length=100), nullable=True))
        
        # Categorização
        batch_op.add_column(sa.Column('categoria_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('subcategoria', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('tags', sa.Text(), nullable=True))
        
        # Identificação Moderna
        batch_op.add_column(sa.Column('codigo_barras', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('qr_code', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('rfid_tag', sa.String(length=100), nullable=True))
        
        # Mídia e Documentos
        batch_op.add_column(sa.Column('imagem_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('manual_url', sa.String(length=500), nullable=True))
        
        # Campos Técnicos
        batch_op.add_column(sa.Column('especificacoes_tecnicas', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('configuracao', sa.Text(), nullable=True))
        
        # Auditoria e Controle
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('created_by', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('updated_by', sa.Integer(), nullable=True))
        
        # Controle de Estado
        batch_op.add_column(sa.Column('ativo', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('bloqueado', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('motivo_bloqueio', sa.String(length=200), nullable=True))
    
    print("✅ Tabela EQUIPAMENTO atualizada - 27 campos adicionados")
    
    # ==================================================
    # TABELA USUARIO - Adicionar campos novos
    # ==================================================
    print("📊 Atualizando tabela USUARIO...")
    
    with op.batch_alter_table('usuario', schema=None) as batch_op:
        batch_op.add_column(sa.Column('email', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('nome_completo', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('departamento', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('ativo', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('last_login', sa.DateTime(), nullable=True))
    
    print("✅ Tabela USUARIO atualizada - 6 campos adicionados")
    
    # ==================================================
    # CRIAR TABELAS NOVAS
    # ==================================================
    
    # Tabela CATEGORIA
    print("📊 Criando tabela CATEGORIA...")
    op.create_table('categoria',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('icone', sa.String(length=50), nullable=True),
        sa.Column('cor', sa.String(length=7), nullable=True),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('ativo', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nome')
    )
    print("✅ Tabela CATEGORIA criada")
    
    # Tabela FORNECEDOR
    print("📊 Criando tabela FORNECEDOR...")
    op.create_table('fornecedor',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=200), nullable=False),
        sa.Column('cnpj', sa.String(length=18), nullable=True),
        sa.Column('email', sa.String(length=120), nullable=True),
        sa.Column('telefone', sa.String(length=20), nullable=True),
        sa.Column('endereco', sa.Text(), nullable=True),
        sa.Column('contato_principal', sa.String(length=200), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('ativo', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    print("✅ Tabela FORNECEDOR criada")
    
    # Tabela HISTORICO_EQUIPAMENTO
    print("📊 Criando tabela HISTORICO_EQUIPAMENTO...")
    op.create_table('historico_equipamento',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('equipamento_id', sa.Integer(), nullable=False),
        sa.Column('acao', sa.String(length=100), nullable=False),
        sa.Column('campo_alterado', sa.String(length=100), nullable=True),
        sa.Column('valor_anterior', sa.Text(), nullable=True),
        sa.Column('valor_novo', sa.Text(), nullable=True),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('data_acao', sa.DateTime(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.ForeignKeyConstraint(['equipamento_id'], ['equipamento.id_interno'], ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    print("✅ Tabela HISTORICO_EQUIPAMENTO criada")
    
    # Tabela NOTIFICACAO
    print("📊 Criando tabela NOTIFICACAO...")
    op.create_table('notificacao',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('titulo', sa.String(length=200), nullable=False),
        sa.Column('mensagem', sa.Text(), nullable=False),
        sa.Column('tipo', sa.String(length=50), nullable=False),
        sa.Column('lida', sa.Boolean(), nullable=True),
        sa.Column('link_acao', sa.String(length=200), nullable=True),
        sa.Column('equipamento_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('lida_em', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['equipamento_id'], ['equipamento.id_interno'], ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    print("✅ Tabela NOTIFICACAO criada")
    
    # Tabela MANUTENCAO_PROGRAMADA
    print("📊 Criando tabela MANUTENCAO_PROGRAMADA...")
    op.create_table('manutencao_programada',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('equipamento_id', sa.Integer(), nullable=False),
        sa.Column('tipo', sa.String(length=100), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=False),
        sa.Column('data_programada', sa.Date(), nullable=False),
        sa.Column('data_realizada', sa.Date(), nullable=True),
        sa.Column('responsavel_tecnico', sa.String(length=200), nullable=True),
        sa.Column('custo_estimado', sa.Float(), nullable=True),
        sa.Column('custo_real', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['usuario.id'], ),
        sa.ForeignKeyConstraint(['equipamento_id'], ['equipamento.id_interno'], ),
        sa.PrimaryKeyConstraint('id')
    )
    print("✅ Tabela MANUTENCAO_PROGRAMADA criada")
    
    # ==================================================
    # ADICIONAR FOREIGN KEYS NA TABELA EQUIPAMENTO
    # ==================================================
    print("📊 Adicionando Foreign Keys na tabela EQUIPAMENTO...")
    
    with op.batch_alter_table('equipamento', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_equipamento_categoria', 'categoria', ['categoria_id'], ['id'])
        batch_op.create_foreign_key('fk_equipamento_fornecedor', 'fornecedor', ['fornecedor_id'], ['id'])
        batch_op.create_foreign_key('fk_equipamento_created_by', 'usuario', ['created_by'], ['id'])
        batch_op.create_foreign_key('fk_equipamento_updated_by', 'usuario', ['updated_by'], ['id'])
    
    print("✅ Foreign Keys adicionadas")
    
    # ==================================================
    # ATUALIZAR DADOS EXISTENTES COM VALORES PADRÃO
    # ==================================================
    print("📊 Atualizando registros existentes com valores padrão...")
    
    # Atualizar equipamentos existentes
    op.execute("""
        UPDATE equipamento 
        SET 
            ativo = TRUE,
            bloqueado = FALSE,
            vida_util_anos = 5,
            valor_residual = 0.0,
            valor_depreciado = 0.0
        WHERE ativo IS NULL
    """)
    
    # Atualizar usuários existentes
    op.execute("""
        UPDATE usuario 
        SET 
            ativo = TRUE,
            created_at = NOW()
        WHERE ativo IS NULL
    """)
    
    print("✅ Registros existentes atualizados")
    
    print("="*70)
    print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*70)
    print("\n📊 Resumo:")
    print("   • Tabela EQUIPAMENTO: +27 campos")
    print("   • Tabela USUARIO: +6 campos")
    print("   • +5 tabelas novas criadas")
    print("   • TODOS os dados existentes preservados")
    print("\n🎉 Sistema pronto para usar a nova versão!\n")


def downgrade():
    """Reverter as mudanças (remover campos e tabelas adicionados)"""
    
    print("⚠️  Revertendo migração...")
    
    # Remover Foreign Keys
    with op.batch_alter_table('equipamento', schema=None) as batch_op:
        batch_op.drop_constraint('fk_equipamento_updated_by', type_='foreignkey')
        batch_op.drop_constraint('fk_equipamento_created_by', type_='foreignkey')
        batch_op.drop_constraint('fk_equipamento_fornecedor', type_='foreignkey')
        batch_op.drop_constraint('fk_equipamento_categoria', type_='foreignkey')
    
    # Remover tabelas novas
    op.drop_table('manutencao_programada')
    op.drop_table('notificacao')
    op.drop_table('historico_equipamento')
    op.drop_table('fornecedor')
    op.drop_table('categoria')
    
    # Remover campos da tabela usuario
    with op.batch_alter_table('usuario', schema=None) as batch_op:
        batch_op.drop_column('last_login')
        batch_op.drop_column('created_at')
        batch_op.drop_column('ativo')
        batch_op.drop_column('departamento')
        batch_op.drop_column('nome_completo')
        batch_op.drop_column('email')
    
    # Remover campos da tabela equipamento
    with op.batch_alter_table('equipamento', schema=None) as batch_op:
        batch_op.drop_column('motivo_bloqueio')
        batch_op.drop_column('bloqueado')
        batch_op.drop_column('ativo')
        batch_op.drop_column('updated_by')
        batch_op.drop_column('created_by')
        batch_op.drop_column('updated_at')
        batch_op.drop_column('created_at')
        batch_op.drop_column('configuracao')
        batch_op.drop_column('especificacoes_tecnicas')
        batch_op.drop_column('manual_url')
        batch_op.drop_column('imagem_url')
        batch_op.drop_column('rfid_tag')
        batch_op.drop_column('qr_code')
        batch_op.drop_column('codigo_barras')
        batch_op.drop_column('tags')
        batch_op.drop_column('subcategoria')
        batch_op.drop_column('categoria_id')
        batch_op.drop_column('nota_fiscal')
        batch_op.drop_column('fornecedor_id')
        batch_op.drop_column('garantia_ate')
        batch_op.drop_column('proxima_manutencao')
        batch_op.drop_column('condicao')
        batch_op.drop_column('departamento')
        batch_op.drop_column('centro_custo')
        batch_op.drop_column('valor_depreciado')
        batch_op.drop_column('vida_util_anos')
        batch_op.drop_column('valor_residual')
    
    print("✅ Migração revertida - banco restaurado ao estado anterior")
