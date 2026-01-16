# 🎯 GUIA DE IMPLANTAÇÃO - PRESERVANDO SEUS 24 EQUIPAMENTOS E 4 USUÁRIOS

## 📊 SITUAÇÃO ATUAL CONFIRMADA

✅ **Banco de dados Azure analisado:**
- 24 equipamentos cadastrados
- 4 usuários ativos
- Estrutura básica (15 campos no equipamento)

✅ **Nova versão vai:**
- **PRESERVAR** todos os 24 equipamentos
- **PRESERVAR** todos os 4 usuários  
- **ADICIONAR** 27 novos campos (vazios, sem quebrar nada)
- **ADICIONAR** 5 tabelas novas (categoria, fornecedor, histórico, etc)

---

## 🚀 PROCESSO DE IMPLANTAÇÃO (3 Passos)

### PASSO 1: Preparação (5 minutos)

#### 1.1. Backup do Banco (OBRIGATÓRIO)

**Via Azure Portal:**
```
1. Acesse portal.azure.com
2. Vá em "Azure Database for PostgreSQL flexible servers"
3. Selecione "terrano-db"
4. Clique em "Backup and Restore"
5. Clique em "Backup Now"
6. Nome: "pre-migracao-campos-modernos-2026-01-16"
```

**Ou via Azure CLI:**
```bash
az postgres flexible-server backup create \
  --resource-group <seu-resource-group> \
  --name terrano-db \
  --backup-name pre-migracao-campos-modernos
```

#### 1.2. Testar Migração Localmente (Opcional mas Recomendado)

```bash
# No seu projeto local
cd terrano-patrimoniov1

# Ativar ambiente virtual
.\venv\Scripts\Activate

# Aplicar migração em banco local de teste
flask db upgrade

# Se tudo OK, prosseguir para passo 2
```

---

### PASSO 2: Deploy com Migração (10 minutos)

Seu processo atual é via Docker → Git → Azure, correto? Então:

#### 2.1. Commit das Mudanças

```bash
# Adicionar arquivo de migração
git add migrations/versions/adicionar_campos_modernos.py

# Adicionar arquivos da nova versão
git add app.py models.py views.py services.py security.py utils.py

# Commit
git commit -m "Migração segura: adicionar campos modernos preservando dados"

# Push para Azure
git push azure main
```

#### 2.2. A Migração Roda Automaticamente

**Se configurado no seu startup script ou Dockerfile:**
```dockerfile
# No Dockerfile ou startup, deve ter algo como:
CMD flask db upgrade && gunicorn --bind 0.0.0.0:8000 app:app
```

**Se NÃO estiver configurado**, adicione ao seu Dockerfile:
```dockerfile
# Antes do CMD, adicione:
RUN flask db upgrade

# Ou no CMD:
CMD ["sh", "-c", "flask db upgrade && gunicorn --bind 0.0.0.0:8000 app:app"]
```

#### 2.3. Monitorar Deploy

```bash
# Ver logs do deploy
az webapp log tail \
  --name <seu-app-name> \
  --resource-group <seu-resource-group>
```

Procure por mensagens como:
```
🚀 Iniciando migração - Adicionando campos modernos...
✅ Tabela EQUIPAMENTO atualizada - 27 campos adicionados
✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!
```

---

### PASSO 3: Validação (5 minutos)

#### 3.1. Acessar Aplicação

```
https://<seu-app>.azurewebsites.net
```

#### 3.2. Checklist de Validação

- [ ] **Site carrega** (não dá erro 500)
- [ ] **Login funciona** com usuário existente
- [ ] **Dashboard mostra** 24 equipamentos
- [ ] **Abrir um equipamento** e ver dados antigos preservados
- [ ] **Campos novos aparecem** (podem estar vazios)
- [ ] **Criar novo equipamento** com campos novos

#### 3.3. Verificar Dados no Banco

Execute novamente:
```bash
python conectar_banco_azure.py
```

Deve mostrar:
- ✅ Equipamento: 24 registros (mesmo número!)
- ✅ Usuario: 4 registros (mesmo número!)
- ✅ Categoria: 0 registros (nova tabela vazia)
- ✅ Fornecedor: 0 registros (nova tabela vazia)
- ✅ 42 campos na tabela equipamento (antes eram 15)

---

## 🎯 O QUE ESPERAR

### Equipamentos Existentes (24):
```
ANTES DO DEPLOY:
id_publico: PAT-001
tipo: Notebook
marca: Dell
valor: 3500.00
localizacao: TI
[15 campos total]

DEPOIS DO DEPLOY:
id_publico: PAT-001  ← PRESERVADO
tipo: Notebook       ← PRESERVADO
marca: Dell          ← PRESERVADO
valor: 3500.00       ← PRESERVADO
localizacao: TI      ← PRESERVADO
categoria_id: NULL   ← NOVO (vazio)
codigo_barras: NULL  ← NOVO (vazio)
qr_code: NULL        ← NOVO (vazio)
ativo: TRUE          ← NOVO (preenchido automaticamente)
[42 campos total]
```

### Usuários Existentes (4):
```
ANTES:
username: admin
password_hash: [hash]
nivel_acesso: 3

DEPOIS:
username: admin          ← PRESERVADO
password_hash: [hash]    ← PRESERVADO
nivel_acesso: 3          ← PRESERVADO
email: NULL              ← NOVO (vazio)
nome_completo: NULL      ← NOVO (vazio)
ativo: TRUE              ← NOVO (preenchido)
```

---

## ✅ GARANTIAS

### 100% Seguro Porque:

1. **Campos novos são NULLABLE**
   - Não requer valor
   - Dados antigos não quebram

2. **Tabelas novas não afetam antigas**
   - Criadas vazias
   - Foreign Keys são opcionais

3. **Migração é ADITIVA**
   - Apenas adiciona
   - Nunca remove ou modifica

4. **Valores padrão automáticos**
   - `ativo = TRUE` para registros antigos
   - `bloqueado = FALSE` para equipamentos
   - `vida_util_anos = 5` como padrão

5. **Rollback disponível**
   - Backup do banco
   - Migração reversível com `flask db downgrade`

---

## 🆘 SE ALGO DER ERRADO

### Problema: Site não carrega (erro 500)

**Solução:**
```bash
# Ver logs
az webapp log tail --name <seu-app> --resource-group <seu-rg>

# Se erro de migração, executar manualmente:
az webapp ssh --name <seu-app> --resource-group <seu-rg>
flask db upgrade
```

### Problema: Migração não rodou

**Solução:**
```bash
# Conectar via SSH ao container
az webapp ssh --name <seu-app> --resource-group <seu-rg>

# Executar migração manualmente
cd /app
flask db upgrade
```

### Problema: Dados sumiram (improvável!)

**Solução:**
```bash
# Restaurar backup
# Via Azure Portal:
1. Azure Database for PostgreSQL
2. terrano-db
3. Backup and Restore
4. Restore
5. Selecionar backup "pre-migracao-campos-modernos"
```

---

## 📊 CRONOGRAMA SUGERIDO

### Melhor Momento:
- **Dia:** Sábado ou Domingo (baixo uso)
- **Horário:** Noite/Madrugada
- **Duração:** 15-20 minutos total

### Timeline:
```
20:00 - Criar backup do banco
20:05 - Fazer commit e push
20:10 - Aguardar deploy
20:15 - Testar aplicação
20:20 - Validar dados
20:25 - Confirmar sucesso ✅
```

---

## 📝 CHECKLIST FINAL

### Antes do Deploy:
- [ ] Backup do banco criado no Azure Portal
- [ ] Arquivo de migração presente em `migrations/versions/`
- [ ] Dockerfile configurado para rodar migração
- [ ] Variáveis de ambiente OK (DATABASE_URL, etc)

### Durante o Deploy:
- [ ] Git push executado
- [ ] Azure recebeu o push
- [ ] Logs mostram migração rodando
- [ ] Logs mostram "MIGRAÇÃO CONCLUÍDA"

### Após o Deploy:
- [ ] Site carrega sem erro 500
- [ ] Login funciona
- [ ] 24 equipamentos aparecem
- [ ] 4 usuários funcionam
- [ ] Novos campos disponíveis
- [ ] Banco verificado com script

---

## 🎉 RESULTADO ESPERADO

```
✅ ANTES:
   • 2 tabelas
   • 24 equipamentos
   • 4 usuários
   • 15 campos por equipamento
   • Funcionalidades básicas

✅ DEPOIS:
   • 7 tabelas (+5 novas)
   • 24 equipamentos (PRESERVADOS!)
   • 4 usuários (PRESERVADOS!)
   • 42 campos por equipamento (+27)
   • Funcionalidades completas + auditoria + segurança
```

---

## 📞 SUPORTE

### Comandos Úteis:

```bash
# Ver logs em tempo real
az webapp log tail --name <app> --resource-group <rg>

# Restart aplicação
az webapp restart --name <app> --resource-group <rg>

# Conectar ao banco (para verificar)
python conectar_banco_azure.py

# Ver status da migração
flask db current
flask db history
```

---

## ✅ PRONTO PARA COMEÇAR?

Execute os 3 passos acima e em 20 minutos você terá:
- ✅ Sistema modernizado
- ✅ Todos os dados preservados
- ✅ Novas funcionalidades disponíveis
- ✅ Zero perda de informação

**Dúvidas?** Execute primeiro o PASSO 1 (backup) - isso já garante 100% de segurança!
