@echo off
REM Script de Deploy para Azure - Versão Windows PowerShell
REM Execute este arquivo .bat no Windows

echo ========================================
echo Deploy Seguro para Azure - Windows
echo ========================================
echo.

REM Verificar se Azure CLI está instalado
where az >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Azure CLI nao encontrado!
    echo Instale em: https://docs.microsoft.com/cli/azure/install-azure-cli
    pause
    exit /b 1
)

REM Login no Azure
echo Verificando autenticacao Azure...
az account show >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Fazendo login no Azure...
    az login
)

REM Solicitar informações
set /p RESOURCE_GROUP="Nome do Resource Group: "
set /p APP_NAME="Nome do App Service: "

echo.
echo ========================================
echo Configuracao:
echo Resource Group: %RESOURCE_GROUP%
echo App Service: %APP_NAME%
echo ========================================
echo.

REM Criar slot de staging se não existir
echo Verificando slot de staging...
az webapp deployment slot list --name %APP_NAME% --resource-group %RESOURCE_GROUP% --query "[?name=='staging']" -o tsv | findstr staging >nul
if %ERRORLEVEL% NEQ 0 (
    echo Criando slot de staging...
    az webapp deployment slot create --name %APP_NAME% --resource-group %RESOURCE_GROUP% --slot staging --configuration-source %APP_NAME%
    echo [OK] Slot de staging criado
) else (
    echo [OK] Slot de staging ja existe
)

REM Criar pacote de deploy
echo.
echo Criando pacote de deploy...
set DEPLOY_FILE=deploy-package-%date:~-4,4%%date:~-7,2%%date:~-10,2%.zip

REM Criar zip (requer PowerShell)
powershell -Command "Compress-Archive -Path app.py,models.py,views.py,services.py,security.py,utils.py,config.py,logging_config_simple.py,requirements.txt,templates,static,migrations -DestinationPath %DEPLOY_FILE% -Force"

echo [OK] Pacote criado: %DEPLOY_FILE%

REM Deploy no staging
echo.
echo Fazendo deploy no slot de staging...
az webapp deployment source config-zip --resource-group %RESOURCE_GROUP% --name %APP_NAME% --slot staging --src %DEPLOY_FILE%

echo.
echo [OK] Deploy no staging concluido!
echo.
echo ========================================
echo Deploy em STAGING concluido!
echo ========================================
echo.
echo Acesse o staging em:
echo https://%APP_NAME%-staging.azurewebsites.net
echo.
echo PROXIMOS PASSOS:
echo 1. Teste a aplicacao no staging
echo 2. Valide login, CRUD, relatorios
echo 3. Se tudo OK, execute: swap-production.bat
echo.
echo ========================================
echo.

set /p SWAP_NOW="Deseja fazer o SWAP para producao agora? (S/N): "
if /I "%SWAP_NOW%"=="S" (
    echo.
    echo [ATENCAO] Fazendo SWAP para PRODUCAO!
    set /p CONFIRMACAO="Tem certeza? Digite 'CONFIRMO' para continuar: "
    
    if "%CONFIRMACAO%"=="CONFIRMO" (
        echo Fazendo swap...
        az webapp deployment slot swap --resource-group %RESOURCE_GROUP% --name %APP_NAME% --slot staging
        
        echo.
        echo ========================================
        echo [OK] SWAP CONCLUIDO! Nova versao em PRODUCAO!
        echo ========================================
        echo.
        echo Producao: https://%APP_NAME%.azurewebsites.net
        echo.
        echo Monitore os logs:
        echo az webapp log tail --name %APP_NAME% --resource-group %RESOURCE_GROUP%
        echo.
    ) else (
        echo Swap cancelado.
    )
) else (
    echo OK! Teste o staging e use swap-production.bat quando estiver pronto.
)

echo.
pause
