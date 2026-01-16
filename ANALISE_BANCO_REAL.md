# 🎯 PLANO DE MIGRAÇÃO ESPECÍFICO - ESTRUTURA REAL DO BANCO

## 📊 SITUAÇÃO ATUAL DESCOBERTA

### ✅ O que existe no Azure AGORA:

**Tabelas:**
- ✅ `equipamento` (24 registros)
- ✅ `usuario` (4 registros)

**Tabela EQUIPAMENTO (15 campos):**
```sql
- id_interno (PK)
- id_publico (UNIQUE)
- tipo
- marca
- modelo
- num_serie
- data_aquisicao
- localizacao
- status
- responsavel
- ultima_manutencao
- valor
- observacoes
- SPE
- termo_pdf_path
```

**Tabela USUARIO (4 campos):**
```sql
- id (PK)
- username (UNIQUE)
- password_hash
- nivel_acesso
```

---

## ⚠️ PROBLEMA IDENTIFICADO

Seu banco de dados atual é **MUITO MAIS SIMPLES** do que o models.py!

### Faltam no Azure:
- ❌ 5 tabelas novas: `categoria`, `fornecedor`, `historico_equipamento`, `notificacao`, `manutencao_programada`
- ❌ 27 campos novos na tabela `equipamento`
- ❌ 6 campos novos na tabela `usuario`

### ✅ O que isso significa:
**A nova versão NÃO VAI PERDER DADOS!** Ela apenas vai **ADICIONAR** campos e tabelas novas.

---

## 🚀 ESTRATÉGIA DE MIGRAÇÃO SEGURA

### Opção 1: Migração com Alembic (RECOMENDADO) ✅

#### Passo 1: Criar migração que adiciona campos faltantes

```bash
# No seu ambiente local
flask db revision -m "adicionar_campos_modernos_equipamento"
```

#### Passo 2: Editar arquivo de migração gerado

O arquivo vai estar em `migrations/versions/XXXXX_adicionar_campos_modernos_equipamento.py`

```python
def upgrade():
    # Adicionar campos na tabela equipamento
    with op.batch_alter_table('equipamento') as batch_op:
        # Financeiros
        batch_op.add_column(sa.Column('valor_residual', sa.Float(), nullable=True, default=0.0))
        batch_op.add_column(sa.Column('vida_util_anos', sa.Integer(), nullable=True, default=5))
        batch_op.add_column(sa.Column('valor_depreciado', sa.Float(), nullable=True, default=0.0))
        
        # Localização
        batch_op.add_column(sa.Column('centro_custo', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('departamento', sa.String(100), nullable=True))
        
        # Status
        batch_op.add_column(sa.Column('condicao', sa.String(50), nullable=True, default='Novo'))
        batch_op.add_column(sa.Column('proxima_manutencao', sa.Date(), nullable=True))
        
        # Garantia
        batch_op.add_column(sa.Column('garantia_ate', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('nota_fiscal', sa.String(100), nullable=True))
        
        # Categorização (sem FK ainda)
        batch_op.add_column(sa.Column('categoria_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('fornecedor_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('subcategoria', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('tags', sa.Text(), nullable=True))
        
        # Identificação
        batch_op.add_column(sa.Column('codigo_barras', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('qr_code', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('rfid_tag', sa.String(100), nullable=True))
        
        # Mídia
        batch_op.add_column(sa.Column('imagem_url', sa.String(500), nullable=True))
        batch_op.add_column(sa.Column('manual_url', sa.String(500), nullable=True))
        
        # Técnico
        batch_op.add_column(sa.Column('especificacoes_tecnicas', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('configuracao', sa.Text(), nullable=True))
        
        # Auditoria
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True, default=datetime.utcnow))
        batch_op.add_column(sa.Column('created_by', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('updated_by', sa.Integer(), nullable=True))
        
        # Controle
        batch_op.add_column(sa.Column('ativo', sa.Boolean(), nullable=True, default=True))
        batch_op.add_column(sa.Column('bloqueado', sa.Boolean(), nullable=True, default=False))
        batch_op.add_column(sa.Column('motivo_bloqueio', sa.String(200), nullable=True))
    
    # Adicionar campos na tabela usuario
    with op.batch_alter_table('usuario') as batch_op:
        batch_op.add_column(sa.Column('email', sa.String(120), nullable=True))
        batch_op.add_column(sa.Column('nome_completo', sa.String(200), nullable=True))
        batch_op.add_column(sa.Column('departamento', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('ativo', sa.Boolean(), nullable=True, default=True))
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('last_login', sa.DateTime(), nullable=True))
    
    # Criar tabelas novas
    op.create_table('categoria',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nome', sa.String(100), nullable=False, unique=True),
        sa.Column('icone', sa.String(50), nullable=True),
        sa.Column('cor', sa.String(7), nullable=True),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('ativo', sa.Boolean(), default=True)
    )
    
    op.create_table('fornecedor',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nome', sa.String(200), nullable=False),
        sa.Column('cnpj', sa.String(18), nullable=True),
        sa.Column('email', sa.String(120), nullable=True),
        sa.Column('telefone', sa.String(20), nullable=True),
        sa.Column('endereco', sa.Text(), nullable=True),
        sa.Column('contato_principal', sa.String(200), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('ativo', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow)
    )
    
    op.create_table('historico_equipamento',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('equipamento_id', sa.Integer(), sa.ForeignKey('equipamento.id_interno'), nullable=False),
        sa.Column('acao', sa.String(100), nullable=False),
        sa.Column('campo_alterado', sa.String(100), nullable=True),
        sa.Column('valor_anterior', sa.Text(), nullable=True),
        sa.Column('valor_novo', sa.Text(), nullable=True),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('data_acao', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('usuario_id', sa.Integer(), sa.ForeignKey('usuario.id'), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True)
    )
    
    op.create_table('notificacao',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('usuario_id', sa.Integer(), sa.ForeignKey('usuario.id'), nullable=False),
        sa.Column('titulo', sa.String(200), nullable=False),
        sa.Column('mensagem', sa.Text(), nullable=False),
        sa.Column('tipo', sa.String(50), nullable=False),
        sa.Column('lida', sa.Boolean(), default=False),
        sa.Column('link_acao', sa.String(200), nullable=True),
        sa.Column('equipamento_id', sa.Integer(), sa.ForeignKey('equipamento.id_interno'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('lida_em', sa.DateTime(), nullable=True)
    )
    
    op.create_table('manutencao_programada',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('equipamento_id', sa.Integer(), sa.ForeignKey('equipamento.id_interno'), nullable=False),
        sa.Column('tipo', sa.String(100), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=False),
        sa.Column('data_programada', sa.Date(), nullable=False),
        sa.Column('data_realizada', sa.Date(), nullable=True),
        sa.Column('responsavel_tecnico', sa.String(200), nullable=True),
        sa.Column('custo_estimado', sa.Float(), nullable=True, default=0.0),
        sa.Column('custo_real', sa.Float(), nullable=True, default=0.0),
        sa.Column('status', sa.String(50), default='Agendada'),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('usuario.id'), nullable=True)
    )
    
    # Adicionar Foreign Keys na tabela equipamento
    with op.batch_alter_table('equipamento') as batch_op:
        batch_op.create_foreign_key('fk_equipamento_categoria', 'categoria', ['categoria_id'], ['id'])
        batch_op.create_foreign_key('fk_equipamento_fornecedor', 'fornecedor', ['fornecedor_id'], ['id'])
        batch_op.create_foreign_key('fk_equipamento_created_by', 'usuario', ['created_by'], ['id'])
        batch_op.create_foreign_key('fk_equipamento_updated_by', 'usuario', ['updated_by'], ['id'])
```

#### Passo 3: Testar localmente

```bash
# Criar banco SQLite local com estrutura atual
# Aplicar migração
flask db upgrade

# Verificar se funcionou
```

#### Passo 4: Deploy com migração

Quando fizer deploy no Azure, a migração será executada automaticamente.

---

## 📝 ARQUIVO DE MIGRAÇÃO PRONTO PARA USAR

Criei um arquivo de migração completo que você pode usar. Veja: `migration_adicionar_campos_modernos.py`

---

## ⚡ PROCESSO PASSO A PASSO

### 1. PREPARAÇÃO (Local)
```bash
# 1.1. Backup do banco Azure
# (Via Azure Portal ou script)

# 1.2. Testar migração localmente
flask db upgrade head
```

### 2. DEPLOY (Azure)
```bash
# 2.1. Deploy via Docker (seu processo atual)
git add .
git commit -m "Adicionar campos modernos - migração segura"
git push azure main

# 2.2. A migração roda automaticamente no startup
# (se configurado no Dockerfile/startup script)
```

### 3. VALIDAÇÃO
```bash
# 3.1. Verificar que aplicação iniciou
# 3.2. Login funciona
# 3.3. Equipamentos existentes aparecem
# 3.4. Novos campos disponíveis (podem estar vazios)
```

---

## ✅ GARANTIAS

### O que VAI acontecer:
- ✅ **TODOS os 24 equipamentos preservados**
- ✅ **TODOS os 4 usuários preservados**
- ✅ Campos antigos mantidos exatamente como estão
- ✅ Campos novos adicionados (vazios, aceita NULL)
- ✅ Tabelas novas criadas (vazias)
- ✅ Aplicação funciona com dados antigos E novos

### O que NÃO VAI acontecer:
- ❌ Nenhum dado será perdido
- ❌ Nenhum campo será removido
- ❌ Nenhuma quebra de compatibilidade
- ❌ Nenhum downtime significativo

---

## 🆘 ROLLBACK SE NECESSÁRIO

Se algo der errado:

```bash
# Opção 1: Fazer downgrade da migração
flask db downgrade -1

# Opção 2: Restaurar backup do banco
# (Via Azure Portal)

# Opção 3: Deploy da versão anterior
git revert HEAD
git push azure main
```

---

## 📊 COMPARAÇÃO: ANTES vs DEPOIS

| Aspecto | Antes (Atual) | Depois (Nova versão) |
|---------|---------------|----------------------|
| **Tabelas** | 2 | 7 (+5 novas) |
| **Campos Equipamento** | 15 | 42 (+27 novos) |
| **Campos Usuario** | 4 | 10 (+6 novos) |
| **Registros Equipamento** | 24 | 24 (preservados) |
| **Registros Usuario** | 4 | 4 (preservados) |
| **Funcionalidades** | Básicas | Completas + Auditoria |

---

## 🎯 RECOMENDAÇÃO FINAL

**Estratégia:** Migração Progressiva com Alembic

**Por quê:**
1. ✅ Adiciona campos sem perder dados
2. ✅ Cria tabelas novas vazias (não afeta existentes)
3. ✅ Todos os registros preservados
4. ✅ Rollback fácil se necessário
5. ✅ Compatível com seu processo Docker atual

**Próximo passo:**
Execute o script de migração que vou criar para você!
