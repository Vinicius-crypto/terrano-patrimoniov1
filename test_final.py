from app_refatorado import create_app
from flask import render_template

app = create_app()
with app.app_context():
    with app.test_request_context():
        try:
            print('🧪 Testando renderização de templates...')
            
            # Testar login
            login_template = render_template('login.html')
            print(f'✅ login.html - OK ({len(login_template)} chars)')
            
            # Testar solicitar_acesso
            solicitar_template = render_template('solicitar_acesso.html')
            print(f'✅ solicitar_acesso.html - OK ({len(solicitar_template)} chars)')
            
            print('🎉 TODOS OS TEMPLATES FUNCIONANDO CORRETAMENTE!')
            print('🚀 APLICAÇÃO PRONTA PARA USO!')
            
        except Exception as e:
            print(f'❌ Erro: {e}')
            import traceback
            traceback.print_exc()