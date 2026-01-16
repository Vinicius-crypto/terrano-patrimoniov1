@echo off
REM Script para fazer SWAP do Staging para Producao - Windows

echo ========================================
echo SWAP: Staging para Producao
echo ========================================
echo.

set /p RESOURCE_GROUP="Nome do Resource Group: "
set /p APP_NAME="Nome do App Service: "

echo.
echo [ATENCAO] Esta acao vai trocar STAGING com PRODUCAO!
echo.
echo Staging atual -^> vai para Producao
echo Producao atual -^> vai para Staging
echo.

set /p CONFIRMACAO="Digite 'CONFIRMO' para continuar: "

if NOT "%CONFIRMACAO%"=="CONFIRMO" (
    echo Operacao cancelada.
    pause
    exit /b 0
)

echo.
echo Executando swap...
az webapp deployment slot swap --resource-group %RESOURCE_GROUP% --name %APP_NAME% --slot staging

echo.
echo ========================================
echo [OK] SWAP CONCLUIDO COM SUCESSO!
echo ========================================
echo.
echo Nova versao em producao:
echo https://%APP_NAME%.azurewebsites.net
echo.
echo Monitorar logs em tempo real:
echo az webapp log tail --name %APP_NAME% --resource-group %RESOURCE_GROUP%
echo.
echo Se precisar fazer ROLLBACK:
echo Execute este script novamente (vai trocar de volta)
echo.
echo ========================================
echo.
pause
