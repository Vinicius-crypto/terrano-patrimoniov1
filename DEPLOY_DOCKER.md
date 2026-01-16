# Deploy Docker - Sistema de Controle de Patrimônio

## 📋 Pré-requisitos

- Docker instalado ([Download](https://www.docker.com/products/docker-desktop))
- Docker Compose instalado (já incluído no Docker Desktop)
- Arquivo `.env` configurado com as credenciais do Azure PostgreSQL

## 🚀 Opção 1: Deploy com Docker Compose (Recomendado)

### 1. Verificar o arquivo .env

Certifique-se que o `.env` existe e contém:

```env
DATABASE_URL=postgresql://vinicius:XFmkbizvA2gL@terrano-db.postgres.database.azure.com:5432/flexibleserverdb
SECRET_KEY=sua-chave-secreta-aqui
AZURE_STORAGE_CONNECTION_STRING=sua-connection-string-azure
```

### 2. Build e Start do Container

```bash
# Build da imagem
docker-compose build

# Iniciar o container
docker-compose up -d

# Ver logs
docker-compose logs -f web
```

### 3. Verificar se está funcionando

Acesse: **http://localhost:8000**

### 4. Comandos úteis

```bash
# Parar o container
docker-compose down

# Reiniciar
docker-compose restart

# Ver status
docker-compose ps

# Entrar no container
docker-compose exec web bash

# Ver logs em tempo real
docker-compose logs -f web
```

## 🐳 Opção 2: Deploy com Docker (sem compose)

### 1. Build da imagem

```bash
docker build -t terrano-patrimonio:latest .
```

### 2. Executar o container

```bash
docker run -d \
  --name terrano-patrimonio \
  -p 8000:8000 \
  --env-file .env \
  -v ${PWD}/uploads:/app/uploads \
  -v ${PWD}/logs:/app/logs \
  --restart unless-stopped \
  terrano-patrimonio:latest
```

### 3. Comandos úteis

```bash
# Ver logs
docker logs -f terrano-patrimonio

# Parar
docker stop terrano-patrimonio

# Iniciar
docker start terrano-patrimonio

# Remover
docker rm -f terrano-patrimonio

# Entrar no container
docker exec -it terrano-patrimonio bash
```

## ☁️ Deploy no Azure Container Instance

### 1. Login no Azure

```bash
az login
```

### 2. Criar Container Registry (se não existir)

```bash
# Criar resource group
az group create --name terrano-rg --location eastus

# Criar ACR
az acr create --resource-group terrano-rg --name terranoacr --sku Basic
```

### 3. Build e Push para ACR

```bash
# Login no ACR
az acr login --name terranoacr

# Build e push
az acr build --registry terranoacr --image terrano-patrimonio:latest .
```

### 4. Deploy no Container Instance

```bash
# Obter credenciais do ACR
ACR_PASSWORD=$(az acr credential show --name terranoacr --query "passwords[0].value" -o tsv)

# Criar container instance
az container create \
  --resource-group terrano-rg \
  --name terrano-patrimonio-app \
  --image terranoacr.azurecr.io/terrano-patrimonio:latest \
  --registry-login-server terranoacr.azurecr.io \
  --registry-username terranoacr \
  --registry-password $ACR_PASSWORD \
  --dns-name-label terrano-patrimonio \
  --ports 8000 \
  --environment-variables \
    FLASK_ENV=production \
  --secure-environment-variables \
    DATABASE_URL="postgresql://vinicius:XFmkbizvA2gL@terrano-db.postgres.database.azure.com:5432/flexibleserverdb" \
    SECRET_KEY="sua-chave-secreta" \
  --cpu 1 \
  --memory 1.5
```

### 5. Verificar deployment

```bash
# Ver status
az container show --resource-group terrano-rg --name terrano-patrimonio-app --query "{FQDN:ipAddress.fqdn,ProvisioningState:provisioningState}" --out table

# Ver logs
az container logs --resource-group terrano-rg --name terrano-patrimonio-app
```

Acesse: **http://terrano-patrimonio.eastus.azurecontainer.io:8000**

## 🌐 Deploy no Azure Web App (Container)

### 1. Criar App Service Plan

```bash
az appservice plan create \
  --name terrano-plan \
  --resource-group terrano-rg \
  --is-linux \
  --sku B1
```

### 2. Criar Web App

```bash
az webapp create \
  --resource-group terrano-rg \
  --plan terrano-plan \
  --name terrano-patrimonio-app \
  --deployment-container-image-name terranoacr.azurecr.io/terrano-patrimonio:latest
```

### 3. Configurar ACR Credentials

```bash
az webapp config container set \
  --name terrano-patrimonio-app \
  --resource-group terrano-rg \
  --docker-custom-image-name terranoacr.azurecr.io/terrano-patrimonio:latest \
  --docker-registry-server-url https://terranoacr.azurecr.io \
  --docker-registry-server-user terranoacr \
  --docker-registry-server-password $ACR_PASSWORD
```

### 4. Configurar variáveis de ambiente

```bash
az webapp config appsettings set \
  --resource-group terrano-rg \
  --name terrano-patrimonio-app \
  --settings \
    FLASK_ENV=production \
    DATABASE_URL="postgresql://vinicius:XFmkbizvA2gL@terrano-db.postgres.database.azure.com:5432/flexibleserverdb" \
    SECRET_KEY="sua-chave-secreta" \
    WEBSITES_PORT=8000
```

Acesse: **https://terrano-patrimonio-app.azurewebsites.net**

## 🔧 Troubleshooting

### Container não inicia

```bash
# Ver logs detalhados
docker logs terrano-patrimonio

# Verificar se a porta está em uso
netstat -ano | findstr :8000
```

### Erro de conexão com banco

- Verifique se o firewall do Azure PostgreSQL permite o IP do container
- Teste a conexão manualmente:

```bash
docker exec -it terrano-patrimonio bash
python -c "import psycopg2; conn = psycopg2.connect('postgresql://vinicius:XFmkbizvA2gL@terrano-db.postgres.database.azure.com:5432/flexibleserverdb'); print('Conectado!')"
```

### Rebuild após mudanças

```bash
# Parar e remover container
docker-compose down

# Rebuild sem cache
docker-compose build --no-cache

# Subir novamente
docker-compose up -d
```

## 📊 Monitoramento

### Health Check

```bash
# Verificar saúde do container
docker inspect --format='{{json .State.Health}}' terrano-patrimonio | python -m json.tool
```

### Métricas

```bash
# Ver uso de recursos
docker stats terrano-patrimonio
```

## 🔐 Segurança

1. **Nunca commite o arquivo .env** - Já está no .gitignore
2. **Use secrets do Docker** para produção:

```bash
echo "sua-senha" | docker secret create db_password -
```

3. **Configure SSL/TLS** com reverse proxy (Nginx/Caddy)

## 🎯 Próximos Passos

- [ ] Configurar CI/CD com GitHub Actions
- [ ] Adicionar HTTPS com Let's Encrypt
- [ ] Configurar backup automático do banco
- [ ] Implementar monitoramento com Azure Monitor
