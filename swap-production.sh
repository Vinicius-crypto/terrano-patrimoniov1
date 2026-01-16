#!/bin/bash
# Script para fazer SWAP do Staging para Produção

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔄 SWAP: Staging → Produção${NC}"
echo "================================================"

# Configurar variáveis
read -p "Nome do Resource Group: " RESOURCE_GROUP
read -p "Nome do App Service: " APP_NAME

# Confirmação
echo ""
echo -e "${RED}⚠️  ATENÇÃO: Esta ação vai trocar STAGING com PRODUÇÃO!${NC}"
echo ""
echo "Staging atual → vai para Produção"
echo "Produção atual → vai para Staging"
echo ""
read -p "Digite 'CONFIRMO' para continuar: " CONFIRMACAO

if [[ $CONFIRMACAO != "CONFIRMO" ]]; then
    echo -e "${YELLOW}Operação cancelada.${NC}"
    exit 0
fi

# Fazer o swap
echo ""
echo -e "${YELLOW}🔄 Executando swap...${NC}"
az webapp deployment slot swap \
    --resource-group $RESOURCE_GROUP \
    --name $APP_NAME \
    --slot staging

echo ""
echo "================================================"
echo -e "${GREEN}✅ SWAP CONCLUÍDO COM SUCESSO!${NC}"
echo ""
echo "🌐 Nova versão em produção:"
echo "   https://$APP_NAME.azurewebsites.net"
echo ""
echo "📊 Monitorar logs em tempo real:"
echo "   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
echo "🔙 Se precisar fazer ROLLBACK:"
echo "   Execute este script novamente (vai trocar de volta)"
echo "================================================"
