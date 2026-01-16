from app_refatorado import create_app
from flask import render_template

app = create_app()
with app.app_context():
    with app.test_request_context():
        try:
            print('🧪 Testando template consulta.html...')
            
            # Renderizar com dados mockados para teste
            template = render_template('consulta.html', resultados=[], busca='')
            print(f'✅ consulta.html - OK ({len(template)} chars)')
            
            print('🎉 TEMPLATE CONSULTA.HTML FUNCIONANDO!')
            
        except Exception as e:
            print(f'❌ Erro: {e}')
            import traceback
            traceback.print_exc()