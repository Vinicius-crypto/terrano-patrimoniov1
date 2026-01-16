#!/bin/bash
# Script de Deploy Seguro para Azure - Opção Blue-Green
# Execute este script para fazer o deploy da nova versão

set -e  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Iniciando Deploy Seguro para Azure${NC}"
echo "================================================"

# 1. Verificar Azure CLI
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI não encontrado. Instale: https://docs.microsoft.com/cli/azure/install-azure-cli${NC}"
    exit 1
fi

# 2. Fazer login no Azure (se necessário)
echo -e "${YELLOW}📝 Verificando autenticação Azure...${NC}"
az account show > /dev/null 2>&1 || az login

# 3. Configurar variáveis (AJUSTE ESSES VALORES!)
read -p "Nome do Resource Group: " RESOURCE_GROUP
read -p "Nome do App Service: " APP_NAME

# 4. Backup do banco de dados
echo -e "${YELLOW}💾 Fazendo backup do banco de dados...${NC}"
BACKUP_NAME="backup-pre-migracao-$(date +%Y%m%d-%H%M%S)"
echo "Backup criado: $BACKUP_NAME"
# Nota: Configure o backup manual no Azure Portal antes

# 5. Criar slot de staging (se não existir)
echo -e "${YELLOW}🔧 Verificando slot de staging...${NC}"
if ! az webapp deployment slot list --name $APP_NAME --resource-group $RESOURCE_GROUP --query "[?name=='staging']" -o tsv | grep -q staging; then
    echo "Criando slot de staging..."
    az webapp deployment slot create \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --slot staging \
        --configuration-source $APP_NAME
    echo -e "${GREEN}✅ Slot de staging criado${NC}"
else
    echo -e "${GREEN}✅ Slot de staging já existe${NC}"
fi

# 6. Criar pacote de deploy
echo -e "${YELLOW}📦 Criando pacote de deploy...${NC}"
DEPLOY_FILE="deploy-package-$(date +%Y%m%d-%H%M%S).zip"

# Criar zip excluindo arquivos desnecessários
zip -r $DEPLOY_FILE \
    app.py \
    models.py \
    views.py \
    services.py \
    security.py \
    utils.py \
    config.py \
    logging_config_simple.py \
    requirements.txt \
    templates/ \
    static/ \
    migrations/ \
    -x "*.pyc" "**/__pycache__/*" ".git/*" "instance/*" "venv/*" "*.md" "tests/*"

echo -e "${GREEN}✅ Pacote criado: $DEPLOY_FILE${NC}"

# 7. Deploy no slot de staging
echo -e "${YELLOW}🚀 Fazendo deploy no slot de staging...${NC}"
az webapp deployment source config-zip \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --slot staging \
    --src $DEPLOY_FILE

echo -e "${GREEN}✅ Deploy no staging concluído${NC}"

# 8. Aguardar aplicação iniciar
echo -e "${YELLOW}⏳ Aguardando aplicação iniciar (30 segundos)...${NC}"
sleep 30

# 9. Obter URL do staging
STAGING_URL="https://$APP_NAME-staging.azurewebsites.net"
echo ""
echo "================================================"
echo -e "${GREEN}✅ Deploy em STAGING concluído!${NC}"
echo ""
echo -e "🌐 Acesse o staging em: ${YELLOW}$STAGING_URL${NC}"
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo "1. Teste a aplicação no staging"
echo "2. Valide login, CRUD, relatórios"
echo "3. Se tudo OK, execute: ./swap-production.sh"
echo "4. Se houver problemas, o staging não afeta a produção"
echo ""
echo "================================================"

# Perguntar se deseja fazer o swap agora
read -p "Deseja fazer o SWAP para produção agora? (s/N): " SWAP_NOW

if [[ $SWAP_NOW == "s" ]] || [[ $SWAP_NOW == "S" ]]; then
    echo ""
    echo -e "${YELLOW}⚠️  ATENÇÃO: Fazendo SWAP para PRODUÇÃO!${NC}"
    echo "A versão em staging vai substituir a produção..."
    read -p "Tem certeza? Digite 'CONFIRMO' para continuar: " CONFIRMACAO
    
    if [[ $CONFIRMACAO == "CONFIRMO" ]]; then
        echo -e "${YELLOW}🔄 Fazendo swap...${NC}"
        az webapp deployment slot swap \
            --resource-group $RESOURCE_GROUP \
            --name $APP_NAME \
            --slot staging
        
        echo ""
        echo "================================================"
        echo -e "${GREEN}✅ SWAP CONCLUÍDO! Nova versão em PRODUÇÃO!${NC}"
        echo ""
        echo -e "🌐 Produção: ${YELLOW}https://$APP_NAME.azurewebsites.net${NC}"
        echo ""
        echo "📊 Monitore os logs nas próximas horas:"
        echo "az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
        echo "================================================"
    else
        echo -e "${YELLOW}Swap cancelado. Use ./swap-production.sh quando estiver pronto.${NC}"
    fi
else
    echo -e "${YELLOW}OK! Teste o staging e use ./swap-production.sh quando estiver pronto.${NC}"
fi
