#!/usr/bin/env python3
"""
Script de Validação Pré-Deploy
Verifica se todos os requisitos estão OK antes do deploy
"""
import os
import sys
from pathlib import Path

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

def check_ok(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def check_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def check_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def check_files():
    """Verificar se todos os arquivos necessários existem"""
    print_header("VERIFICANDO ARQUIVOS")
    
    required_files = [
        'app.py',
        'models.py',
        'views.py',
        'services.py',
        'security.py',
        'utils.py',
        'config.py',
        'logging_config_simple.py',
        'requirements.txt',
        'Dockerfile',
    ]
    
    required_dirs = [
        'templates',
        'static',
        'migrations',
    ]
    
    all_ok = True
    
    for file in required_files:
        if Path(file).exists():
            check_ok(f"Arquivo encontrado: {file}")
        else:
            check_error(f"Arquivo faltando: {file}")
            all_ok = False
    
    for dir in required_dirs:
        if Path(dir).exists():
            check_ok(f"Diretório encontrado: {dir}/")
        else:
            check_error(f"Diretório faltando: {dir}/")
            all_ok = False
    
    return all_ok

def check_imports():
    """Verificar se todos os imports funcionam"""
    print_header("VERIFICANDO IMPORTS")
    
    all_ok = True
    
    try:
        import flask
        check_ok(f"Flask {flask.__version__} instalado")
    except ImportError:
        check_error("Flask não instalado")
        all_ok = False
    
    try:
        import flask_sqlalchemy
        check_ok("Flask-SQLAlchemy instalado")
    except ImportError:
        check_error("Flask-SQLAlchemy não instalado")
        all_ok = False
    
    try:
        import flask_login
        check_ok("Flask-Login instalado")
    except ImportError:
        check_error("Flask-Login não instalado")
        all_ok = False
    
    try:
        import bcrypt
        check_ok("Bcrypt instalado")
    except ImportError:
        check_error("Bcrypt não instalado")
        all_ok = False
    
    try:
        from azure.storage.blob import BlobServiceClient
        check_ok("Azure Storage Blob instalado")
    except ImportError:
        check_warning("Azure Storage Blob não instalado (OK para desenvolvimento)")
    
    try:
        import reportlab
        check_ok("ReportLab instalado")
    except ImportError:
        check_error("ReportLab não instalado")
        all_ok = False
    
    return all_ok

def check_env_vars():
    """Verificar variáveis de ambiente"""
    print_header("VERIFICANDO VARIÁVEIS DE AMBIENTE")
    
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
    ]
    
    optional_vars = [
        'AZURE_STORAGE_CONNECTION_STRING',
        'FLASK_ENV',
    ]
    
    all_ok = True
    
    for var in required_vars:
        if os.getenv(var):
            check_ok(f"{var} definida")
        else:
            check_error(f"{var} NÃO definida (OBRIGATÓRIA)")
            all_ok = False
    
    for var in optional_vars:
        if os.getenv(var):
            check_ok(f"{var} definida")
        else:
            check_warning(f"{var} não definida (opcional)")
    
    # Verificar DATABASE_URL
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        if 'postgresql' in db_url or 'postgres' in db_url:
            check_ok("DATABASE_URL aponta para PostgreSQL")
        else:
            check_warning(f"DATABASE_URL não parece ser PostgreSQL: {db_url[:30]}...")
    
    return all_ok

def check_code_syntax():
    """Verificar sintaxe dos arquivos Python"""
    print_header("VERIFICANDO SINTAXE DO CÓDIGO")
    
    python_files = [
        'app.py',
        'models.py',
        'views.py',
        'services.py',
        'security.py',
        'utils.py',
        'config.py',
    ]
    
    all_ok = True
    
    for file in python_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                compile(f.read(), file, 'exec')
            check_ok(f"Sintaxe OK: {file}")
        except SyntaxError as e:
            check_error(f"Erro de sintaxe em {file}: {e}")
            all_ok = False
        except FileNotFoundError:
            check_error(f"Arquivo não encontrado: {file}")
            all_ok = False
    
    return all_ok

def check_models_compatibility():
    """Verificar compatibilidade dos modelos"""
    print_header("VERIFICANDO COMPATIBILIDADE DOS MODELOS")
    
    try:
        # Importar os modelos
        import models
        
        # Verificar se as classes existem
        required_models = [
            'Usuario',
            'Equipamento',
            'Categoria',
            'Fornecedor',
            'HistoricoEquipamento',
            'Notificacao',
            'ManutencaoProgramada',
        ]
        
        all_ok = True
        for model_name in required_models:
            if hasattr(models, model_name):
                check_ok(f"Modelo {model_name} encontrado")
            else:
                check_error(f"Modelo {model_name} não encontrado")
                all_ok = False
        
        return all_ok
        
    except Exception as e:
        check_error(f"Erro ao importar models: {e}")
        return False

def check_templates():
    """Verificar templates HTML"""
    print_header("VERIFICANDO TEMPLATES")
    
    required_templates = [
        'base.html',
        'login.html',
        'dashboard.html',
        'cadastro_equipamento.html',
        'consulta.html',
        'cadastro_usuario.html',
    ]
    
    all_ok = True
    templates_dir = Path('templates')
    
    for template in required_templates:
        template_path = templates_dir / template
        if template_path.exists():
            check_ok(f"Template encontrado: {template}")
        else:
            check_error(f"Template faltando: {template}")
            all_ok = False
    
    return all_ok

def check_azure_cli():
    """Verificar se Azure CLI está instalado"""
    print_header("VERIFICANDO AZURE CLI")
    
    import subprocess
    
    try:
        result = subprocess.run(['az', '--version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            check_ok("Azure CLI instalado")
            return True
        else:
            check_error("Azure CLI não responde corretamente")
            return False
    except FileNotFoundError:
        check_error("Azure CLI não encontrado")
        check_warning("Instale em: https://docs.microsoft.com/cli/azure/install-azure-cli")
        return False
    except subprocess.TimeoutExpired:
        check_error("Azure CLI timeout")
        return False

def main():
    print_header("🔍 VALIDAÇÃO PRÉ-DEPLOY - SISTEMA TERRANO PATRIMÔNIO")
    
    results = {
        'Arquivos': check_files(),
        'Imports': check_imports(),
        'Variáveis de Ambiente': check_env_vars(),
        'Sintaxe': check_code_syntax(),
        'Modelos': check_models_compatibility(),
        'Templates': check_templates(),
        'Azure CLI': check_azure_cli(),
    }
    
    print_header("📊 RESUMO DA VALIDAÇÃO")
    
    for check, passed in results.items():
        if passed:
            check_ok(f"{check}: PASSOU")
        else:
            check_error(f"{check}: FALHOU")
    
    all_passed = all(results.values())
    
    print()
    if all_passed:
        print(f"{Colors.GREEN}{'='*60}{Colors.END}")
        print(f"{Colors.GREEN}✅ TODAS AS VALIDAÇÕES PASSARAM!{Colors.END}")
        print(f"{Colors.GREEN}{'='*60}{Colors.END}")
        print(f"\n{Colors.GREEN}Você está pronto para fazer o deploy!{Colors.END}")
        print(f"{Colors.BLUE}Execute: deploy-azure-staging.bat (Windows) ou .sh (Linux){Colors.END}\n")
        return 0
    else:
        print(f"{Colors.RED}{'='*60}{Colors.END}")
        print(f"{Colors.RED}❌ ALGUMAS VALIDAÇÕES FALHARAM{Colors.END}")
        print(f"{Colors.RED}{'='*60}{Colors.END}")
        print(f"\n{Colors.YELLOW}Corrija os problemas acima antes de fazer o deploy.{Colors.END}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
