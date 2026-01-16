# 🚀 GUIA RÁPIDO: PREPARAÇÃO E MIGRAÇÃO

## ✅ ANTES DE MIGRAR (FAÇA AGORA)

### 1️⃣ BACKUP NO AZURE PORTAL (CRÍTICO!)

1. Acesse: https://portal.azure.com
2. Navegue: **Azure Database for PostgreSQL flexible servers** → **terrano-db**
3. Menu: **Backup and restore** → **Backup now**
4. Nome: `pre-migracao-modernizacao-20260116`
5. Aguarde confirmação ✅

### 2️⃣ ORGANIZE OS DADOS ATUAIS

**Use a função de edição para revisar os 24 equipamentos:**

http://localhost:5000/consulta → Clique em "✏️ Editar"

**Campos importantes para preencher/verificar AGORA:**
- ✅ **Tipo** - correto?
- ✅ **Categoria** - preenchido?
- ✅ **Responsável** - atualizado?
- ✅ **Localização** - correta?
- ✅ **Status** - Em uso / Estocado / Manutenção?
- ✅ **Marca/Modelo** - completo?
- ✅ **Centro de Custo** - informado?
- ✅ **Observações** - documentado?
- ✅ **Foto** - upload feito?

**Anote equipamentos que precisarão de:**
- Código de barras
- Fornecedor
- Número de série
- Valor de aquisição
- Data de compra

---

## 🎯 EXECUTAR MIGRAÇÃO

### 3️⃣ PARAR O SERVIDOR FLASK

No terminal onde o Flask está rodando:
```
CTRL + C
```

### 4️⃣ EXECUTAR MIGRAÇÃO

```bash
# Ativar ambiente virtual (se não estiver ativo)
venv\Scripts\activate

# Executar migração
flask db upgrade

# Verificar sucesso
```

**O que acontece:**
- ✅ Adiciona 27 novos campos em `equipamento` (todos nullable)
- ✅ Adiciona 6 novos campos em `usuario` (todos nullable)
- ✅ Cria 5 novas tabelas: categoria, fornecedor, historico, notificacao, manutencao
- ✅ **PRESERVA TODOS OS 24 EQUIPAMENTOS E 4 USUÁRIOS**

### 5️⃣ VERIFICAR SUCESSO

```bash
# Reiniciar Flask
python app.py
```

Acesse: http://localhost:5000/consulta
- ✅ Todos os 24 equipamentos devem aparecer
- ✅ Dados devem estar intactos
- ✅ Botão "Editar" funcionando

### 6️⃣ PREENCHER NOVOS CAMPOS (APÓS MIGRAÇÃO)

Use a edição para adicionar nos equipamentos:
- 🆕 Código de barras
- 🆕 Número de série
- 🆕 Fornecedor
- 🆕 Valor de aquisição
- 🆕 Data de aquisição
- 🆕 Nota fiscal
- 🆕 Garantia até
- 🆕 Especificações técnicas
- 🆕 Condição física

---

## 🚨 SE ALGO DER ERRADO

### Reverter Migração:
```bash
flask db downgrade
```

### Restaurar Backup:
1. Azure Portal → **terrano-db**
2. **Backup and restore** → **Restore**
3. Selecione: `pre-migracao-modernizacao-20260116`

---

## 📊 RESUMO DO QUE SERÁ ADICIONADO

### Equipamento: +27 campos
- Financeiros: valor_residual, vida_util_anos, valor_depreciado
- Localização: centro_custo, departamento
- Status: condicao, proxima_manutencao
- Garantia: garantia_ate, fornecedor_id, nota_fiscal
- Identificação: codigo_barras, qr_code, numero_serie
- Técnicos: especificacoes_tecnicas, capacidade, voltagem, potencia
- Imagens: image_path, image_url
- Auditoria: created_by, updated_by, created_at, updated_at
- Outros: subcategoria, tags, prioridade

### Usuário: +6 campos
- email, nome_completo, departamento
- ativo, created_at, last_login

### Novas Tabelas:
- **categoria** - organizar equipamentos
- **fornecedor** - cadastro de fornecedores
- **historico_equipamento** - log de alterações
- **notificacao** - alertas de manutenção
- **manutencao_programada** - agenda de manutenções

---

## ✅ CHECKLIST FINAL

- [ ] Backup feito no Azure Portal
- [ ] Dados atuais revisados e atualizados
- [ ] Servidor Flask parado
- [ ] Migração executada (`flask db upgrade`)
- [ ] Verificação: 24 equipamentos preservados
- [ ] Servidor Flask reiniciado
- [ ] Teste de edição funcionando
- [ ] Novos campos sendo preenchidos

---

**🎉 Pronto para começar? Siga os passos 1 e 2 primeiro!**
