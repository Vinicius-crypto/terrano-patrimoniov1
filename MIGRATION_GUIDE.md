# Exemplo de Migração Segura - Novos Campos

## Campos Sugeridos para Adicionar (Fase 1)

### Equipamento - Novos campos:
```python
# Campos para melhorar o controle
codigo_barras = db.Column(db.String(100), nullable=True)
garantia_ate = db.Column(db.Date, nullable=True)
centro_custo = db.Column(db.String(100), nullable=True)
fornecedor = db.Column(db.String(200), nullable=True)

# Campos de auditoria
created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
updated_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)
created_by = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
updated_by = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)

# Campos para categorização
categoria = db.Column(db.String(100), nullable=True)  # Hardware, Software, Mobiliário
subcategoria = db.Column(db.String(100), nullable=True)
tags = db.Column(db.Text, nullable=True)  # JSON: ["urgente", "critico", "novo"]

# Campos financeiros
valor_residual = db.Column(db.Float, nullable=True, default=0.0)
vida_util_anos = db.Column(db.Integer, nullable=True, default=5)
```

## Processo Passo-a-Passo:

### 1. Backup
```bash
# PostgreSQL
pg_dump $DATABASE_URL > backup_pre_migration_$(date +%Y%m%d_%H%M%S).sql

# Se for SQLite local (desenvolvimento)
cp database.db database_backup_$(date +%Y%m%d_%H%M%S).db
```

### 2. Modificar Modelo
```python
# No app.py, adicionar os novos campos ao modelo Equipamento
# IMPORTANTE: Todos com nullable=True ou default value
```

### 3. Gerar Migração
```bash
flask db migrate -m "Add audit and control fields to Equipamento"
```

### 4. Revisar Migração Gerada
```python
# Arquivo gerado em migrations/versions/xxxx_add_audit_fields.py
def upgrade():
    # Verificar se os comandos estão corretos
    op.add_column('equipamento', sa.Column('codigo_barras', sa.String(100), nullable=True))
    op.add_column('equipamento', sa.Column('garantia_ate', sa.Date(), nullable=True))
    # etc...

def downgrade():
    # Comandos para reverter
    op.drop_column('equipamento', 'tags')
    op.drop_column('equipamento', 'garantia_ate')
    # etc...
```

### 5. Aplicar Migração
```bash
# Aplicar em desenvolvimento primeiro
flask db upgrade

# Se tudo OK, aplicar em produção
FLASK_ENV=production flask db upgrade
```

### 6. Atualizar Dados Existentes (Opcional)
```python
# Script para popular campos novos com dados padrão
with app.app_context():
    equipamentos = Equipamento.query.all()
    for eq in equipamentos:
        if not eq.created_at:
            eq.created_at = datetime.utcnow()
        if not eq.categoria:
            eq.categoria = "Hardware"  # valor padrão baseado no tipo
        if not eq.vida_util_anos:
            eq.vida_util_anos = 5
    db.session.commit()
```

## Estratégia de Rollback:

```bash
# Se algo der errado:
flask db downgrade  # Volta uma migração
flask db downgrade <revision_id>  # Volta para revisão específica

# Restaurar backup se necessário:
psql $DATABASE_URL < backup_pre_migration_20241008_143000.sql
```

## Vantagens desta Abordagem:

✅ **Preserva dados existentes**
✅ **Permite rollback seguro**
✅ **Versionamento controlado**
✅ **Pode ser testado em desenvolvimento**
✅ **Não quebra funcionalidades atuais**