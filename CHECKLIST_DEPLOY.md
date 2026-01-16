# 🚀 Checklist de Deploy - Docker → GitHub → Azure

## ✅ Status Atual

### Workflow GitHub Actions
- **Arquivo**: `.github/workflows/main_terrano-patrimonio.yml`
- **Trigger**: Push na branch `main`
- **Fluxo**: 
  1. Build da imagem Docker
  2. Push para Docker Hub (viniciuscrypto1/terrano-backend-v2:latest)
  3. Deploy no Azure App Service (terrano-backend-v2)

### Secrets Necessários no GitHub
Verifique se estão configurados em: `Settings → Secrets and variables → Actions`

- [ ] `DOCKERHUB_USERNAME` - Seu usuário do Docker Hub
- [ ] `DOCKERHUB_PASSWORD` - Senha ou token do Docker Hub
- [ ] `AZURE_CREDENTIALS` - Credenciais do Azure (Service Principal)

## 📋 Pré-Deploy Checklist

### 1. Verificar Arquivos Essenciais
- [x] `Dockerfile` - Configurado e funcional
- [x] `.dockerignore` - Otimizado
- [x] `docker-compose.yml` - Para testes locais
- [x] `.env` - Com variáveis corretas (NÃO commitar!)
- [x] `requirements.txt` - Todas dependências listadas

### 2. Configuração no Azure App Service

Execute no Azure Portal ou CLI:

```bash
# Configurar variáveis de ambiente no Azure App Service
az webapp config appsettings set \
  --name terrano-backend-v2 \
  --resource-group <SEU_RESOURCE_GROUP> \
  --settings \
    FLASK_ENV=production \
    DATABASE_URL="postgresql://vinicius:XFmkbizvA2gL@terrano-db.postgres.database.azure.com:5432/flexibleserverdb" \
    SECRET_KEY="<GERAR_NOVA_CHAVE>" \
    WEBSITES_PORT=8000
```

### 3. Testar Localmente com Docker (Opcional)

**Inicie o Docker Desktop** primeiro, depois:

```bash
# Build local
docker-compose build

# Executar
docker-compose up -d

# Testar
curl http://localhost:8000

# Ver logs
docker-compose logs -f web

# Parar
docker-compose down
```

## 🎯 Processo de Deploy

### Opção 1: Deploy Automático (Recomendado)

```bash
# 1. Commit todas as mudanças
git add .
git commit -m "feat: adiciona modais de fornecedor/categoria + docker deploy"

# 2. Push para main (triggera o workflow)
git push origin main

# 3. Acompanhar o deploy
# Acesse: https://github.com/SEU_USER/SEU_REPO/actions
```

### Opção 2: Deploy Manual via Azure CLI

```bash
# Login no Azure
az login

# Pull da imagem do Docker Hub
az webapp config container set \
  --name terrano-backend-v2 \
  --resource-group <SEU_RESOURCE_GROUP> \
  --docker-custom-image-name viniciuscrypto1/terrano-backend-v2:latest \
  --docker-registry-server-url https://index.docker.io

# Reiniciar o app
az webapp restart --name terrano-backend-v2 --resource-group <SEU_RESOURCE_GROUP>
```

## 🔍 Verificação Pós-Deploy

### 1. Verificar logs no Azure

```bash
# Ver logs em tempo real
az webapp log tail --name terrano-backend-v2 --resource-group <SEU_RESOURCE_GROUP>

# Ou via portal
# Portal Azure → App Service → Log stream
```

### 2. Testar endpoints

```bash
# Health check
curl https://terrano-backend-v2.azurewebsites.net/

# Login
curl https://terrano-backend-v2.azurewebsites.net/login
```

### 3. Verificar funcionalidades

- [ ] Login funciona
- [ ] Dashboard carrega
- [ ] Cadastro de equipamento funciona
- [ ] Modais de Fornecedor/Categoria funcionam
- [ ] Consulta retorna dados
- [ ] Upload de termos funciona
- [ ] Edição de equipamento funciona

## 🛠️ Troubleshooting

### Erro: "Container didn't respond to HTTP pings"

**Solução**: Verificar se a porta está configurada

```bash
az webapp config appsettings set \
  --name terrano-backend-v2 \
  --resource-group <SEU_RESOURCE_GROUP> \
  --settings WEBSITES_PORT=8000
```

### Erro: Conexão com banco de dados

**Solução**: Verificar variável DATABASE_URL e firewall do PostgreSQL

```bash
# Ver configurações atuais
az webapp config appsettings list \
  --name terrano-backend-v2 \
  --resource-group <SEU_RESOURCE_GROUP>

# Adicionar IP do Azure no firewall do PostgreSQL
az postgres flexible-server firewall-rule create \
  --resource-group <SEU_RESOURCE_GROUP> \
  --name terrano-db \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### Build falha no GitHub Actions

**Solução**: Verificar secrets e logs

1. Acesse: `https://github.com/SEU_USER/SEU_REPO/actions`
2. Clique no workflow com erro
3. Verifique qual step falhou
4. Confirme que os secrets estão configurados

## 📊 Monitoramento

### Métricas importantes

```bash
# Ver uso de recursos
az webapp show \
  --name terrano-backend-v2 \
  --resource-group <SEU_RESOURCE_GROUP> \
  --query "{state:state, outboundIpAddresses:outboundIpAddresses}"
```

### Configurar Application Insights (Opcional)

```bash
# Criar Application Insights
az monitor app-insights component create \
  --app terrano-patrimonio-insights \
  --location eastus \
  --resource-group <SEU_RESOURCE_GROUP>

# Obter instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app terrano-patrimonio-insights \
  --resource-group <SEU_RESOURCE_GROUP> \
  --query instrumentationKey -o tsv)

# Configurar no App Service
az webapp config appsettings set \
  --name terrano-backend-v2 \
  --resource-group <SEU_RESOURCE_GROUP> \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY
```

## 🎉 Próximos Passos

- [ ] Configurar domínio customizado
- [ ] Adicionar SSL/HTTPS (Let's Encrypt ou Azure Managed Certificate)
- [ ] Configurar alertas no Azure Monitor
- [ ] Implementar backup automático do banco
- [ ] Adicionar testes automatizados no CI/CD
- [ ] Documentar procedimentos de rollback

## 📝 Notas Importantes

- ⚠️ **NUNCA** commitar o arquivo `.env` no Git
- ⚠️ Gerar nova `SECRET_KEY` para produção (não usar a mesma de desenvolvimento)
- ⚠️ Configurar firewall do PostgreSQL para aceitar apenas IPs do Azure
- ⚠️ Fazer backup do banco antes de cada deploy
- ✅ Testar localmente antes de fazer push para main
