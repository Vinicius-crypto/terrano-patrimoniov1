@echo off
setlocal

REM === CONFIGURAÇÕES ===
set IMAGE_NAME=viniciuscrypto1/terrano-backend-v2
set TAG=latest

REM === MENSAGEM DE COMMIT ===
set /p COMMIT_MSG=Digite a mensagem de commit: 

REM === BUILD DA IMAGEM DOCKER ===
echo 🔧 Construindo imagem Docker...
docker build -t %IMAGE_NAME%:%TAG% .
IF ERRORLEVEL 1 (
    echo ❌ Erro ao buildar imagem Docker.
    pause
    exit /b 1
)

REM === PUSH PARA DOCKER HUB ===
echo 🚀 Fazendo push para o Docker Hub...
docker push %IMAGE_NAME%:%TAG%
IF ERRORLEVEL 1 (
    echo ❌ Erro ao fazer push da imagem.
    pause
    exit /b 1
)

REM === COMMIT & PUSH PARA GITHUB ===
echo 💾 Fazendo commit e push para o GitHub...
git add .
git commit -m "%COMMIT_MSG%"
git push origin main

echo ✅ Deploy finalizado com sucesso!
pause
