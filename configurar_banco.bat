@echo off
echo ========================================
echo CONFIGURAR SENHA DO BANCO DE DADOS
echo ========================================
echo.
set /p SENHA="Digite a senha do banco PostgreSQL: "
echo.
echo Atualizando arquivo .env...
powershell -Command "(Get-Content .env) -replace 'XFmkbizvA2gL', '%SENHA%' | Set-Content .env"
echo.
echo ✅ Senha configurada!
echo.
echo Reiniciando Flask...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul
python app.py
