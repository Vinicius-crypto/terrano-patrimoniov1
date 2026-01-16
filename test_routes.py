"""
Teste isolado para verificar se os templates estão corretos
"""
from app_refatorado import create_app
from flask import url_for

# Criar aplicação
app = create_app()

# Testar no contexto da aplicação
with app.app_context():
    with app.test_request_context():
        try:
            # Testar se a rota 'home' existe
            home_url = url_for('home')
            print(f"✅ Rota 'home' encontrada: {home_url}")
            
            # Testar se a rota 'login' existe
            login_url = url_for('login')
            print(f"✅ Rota 'login' encontrada: {login_url}")
            
            # Testar se a rota 'logout' existe
            logout_url = url_for('logout')
            print(f"✅ Rota 'logout' encontrada: {logout_url}")
            
            print("✅ Todas as rotas estão configuradas corretamente!")
            
        except Exception as e:
            print(f"❌ Erro ao testar rotas: {e}")

# Listar todas as rotas disponíveis
with app.app_context():
    print("\n📋 Rotas disponíveis:")
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        print(f"  {rule.endpoint}: {rule.rule} [{methods}]")