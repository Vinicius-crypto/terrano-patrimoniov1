from app_refatorado import create_app
from flask import render_template_string, render_template

app = create_app()
with app.app_context():
    with app.test_request_context():
        try:
            result = render_template_string('{{ url_for("home") }}')
            print(f'✅ url_for("home") funciona: {result}')
            
            template = render_template('login.html')
            print('✅ Template login.html renderizado com sucesso!')
            print(f'Tamanho do template: {len(template)} caracteres')
        except Exception as e:
            print(f'❌ Erro: {e}')
            import traceback
            traceback.print_exc()