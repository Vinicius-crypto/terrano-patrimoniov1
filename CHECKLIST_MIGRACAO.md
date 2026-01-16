# ✅ CHECKLIST DE MIGRAÇÃO - SISTEMA TERRANO PATRIMÔNIO v1

## 📋 PRÉ-MIGRAÇÃO

### Backups
- [ ] Backup do banco de dados PostgreSQL criado
  - Nome do backup: ___________________________
  - Data/hora: ___________________________
  
- [ ] Backup do Azure Blob Storage (opcional)
  - [ ] Container 'termos' baixado localmente
  
- [ ] Código atual (app_original.py) salvo como backup
  - [ ] Cópia local em local seguro

### Ambiente Azure
- [ ] Azure CLI instalado e configurado
  - Versão: `az --version`
  
- [ ] Login no Azure realizado
  - `az login` executado com sucesso
  
- [ ] Informações do ambiente anotadas:
  - Resource Group: ___________________________
  - App Service Name: ___________________________
  - PostgreSQL Server: ___________________________
  - Região: ___________________________

### Variáveis de Ambiente
- [ ] SECRET_KEY configurada e segura
- [ ] DATABASE_URL configurada
- [ ] AZURE_STORAGE_CONNECTION_STRING configurada
- [ ] FLASK_ENV=production definida

---

## 🧪 TESTES EM STAGING

### Deploy em Staging
- [ ] Slot de staging criado
- [ ] Deploy realizado: `deploy-azure-staging.bat` ou `.sh`
- [ ] Aplicação iniciou sem erros
- [ ] URL do staging acessível: https://[app-name]-staging.azurewebsites.net

### Testes Funcionais

#### Autenticação
- [ ] Login com usuário existente funciona
- [ ] Login com credenciais inválidas retorna erro apropriado
- [ ] Logout funciona corretamente
- [ ] Sessão persiste após navegação

#### Listagem e Consulta
- [ ] Dashboard carrega com estatísticas corretas
- [ ] Total de equipamentos corresponde ao esperado
- [ ] Listagem de equipamentos exibe dados corretos
- [ ] Busca por ID público funciona
- [ ] Busca por tipo funciona
- [ ] Busca por responsável funciona
- [ ] Filtros funcionam corretamente

#### CRUD de Equipamentos
- [ ] Criar novo equipamento funciona
- [ ] Campos obrigatórios validados
- [ ] Editar equipamento existente funciona
- [ ] Campos editados são salvos corretamente
- [ ] Exclusão de equipamento funciona (se aplicável)
- [ ] Histórico de alterações é registrado

#### Relatórios
- [ ] Exportar CSV funciona
- [ ] CSV contém todos os dados corretos
- [ ] Gerar PDF funciona
- [ ] PDF é formatado corretamente
- [ ] Termo de Cautela pode ser gerado
- [ ] Termo de Cautela contém dados corretos

#### Upload e Visualização
- [ ] Upload de termo de cautela funciona
- [ ] PDF é salvo no Azure Blob Storage
- [ ] Visualização de termo funciona
- [ ] Upload de imagem de equipamento funciona

#### Administração
- [ ] Painel admin acessível (nível 3)
- [ ] Listar usuários funciona
- [ ] Criar novo usuário funciona
- [ ] Editar usuário funciona
- [ ] Ativar/desativar usuário funciona
- [ ] Resetar senha funciona
- [ ] Relatório de usuários funciona

#### APIs
- [ ] `/api/dashboard-stats` retorna JSON correto
- [ ] `/api/search` funciona
- [ ] Dados retornados são precisos

#### Integrações
- [ ] Conexão com PostgreSQL OK
- [ ] Conexão com Azure Blob Storage OK
- [ ] Logs sendo gerados corretamente
- [ ] Nenhum erro crítico nos logs

---

## 🚀 MIGRAÇÃO PARA PRODUÇÃO

### Preparação Final
- [ ] Todos os testes em staging passaram
- [ ] Usuários notificados sobre atualização
- [ ] Janela de manutenção definida (se opção 2)
- [ ] Equipe de suporte em stand-by

### Execução do SWAP
- [ ] Executado `swap-production.bat` ou `.sh`
- [ ] Confirmação digitada corretamente
- [ ] Swap concluído sem erros
- [ ] Aplicação acessível na URL de produção

### Validação Pós-Deploy (15 minutos)
- [ ] Site de produção acessível
- [ ] Login funciona
- [ ] Dashboard carrega
- [ ] Equipamentos visíveis
- [ ] Dados correspondem ao esperado
- [ ] Nenhum erro 500 nos logs

---

## 📊 MONITORAMENTO (PRIMEIRAS 24 HORAS)

### Primeira Hora
- [ ] Logs monitorados continuamente
- [ ] Nenhum erro crítico encontrado
- [ ] Performance aceitável (tempo de resposta < 2s)
- [ ] Usuários conseguindo acessar

### Primeiras 6 Horas
- [ ] Feedback de usuários coletado
- [ ] Funcionalidades principais testadas por usuários reais
- [ ] Nenhum bug crítico reportado
- [ ] Métricas de uso normais

### Primeiras 24 Horas
- [ ] Sistema estável
- [ ] Logs limpos (sem warnings críticos)
- [ ] Performance mantida
- [ ] Usuários satisfeitos

---

## 🆘 PLANO DE ROLLBACK (SE NECESSÁRIO)

### Identificação de Problema
- [ ] Problema crítico identificado
- [ ] Impacto avaliado
- [ ] Decisão de rollback tomada

### Execução do Rollback
- [ ] Executado `swap-production.bat` novamente
- [ ] Versão anterior restaurada
- [ ] Validação da versão antiga funcionando
- [ ] Usuários notificados

### Pós-Rollback
- [ ] Problema documentado
- [ ] Root cause analysis iniciada
- [ ] Correção planejada
- [ ] Nova tentativa agendada

---

## 📝 NOTAS E OBSERVAÇÕES

### Problemas Encontrados:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

### Ajustes Necessários:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

### Lições Aprendidas:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

---

## ✅ ASSINATURAS

**Responsável pelo Deploy:**
Nome: _________________________ Data: ___/___/______

**Validação Técnica:**
Nome: _________________________ Data: ___/___/______

**Aprovação Final:**
Nome: _________________________ Data: ___/___/______

---

## 🎯 STATUS FINAL

- [ ] ✅ Migração concluída com SUCESSO
- [ ] ⚠️ Migração com problemas menores (especificar acima)
- [ ] ❌ Rollback executado (especificar motivo acima)

**Data de conclusão:** ___/___/______
**Versão deployed:** app.py modular v1.0
**Downtime total:** _______ minutos
