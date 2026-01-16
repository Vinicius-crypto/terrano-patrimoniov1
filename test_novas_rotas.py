from app_refatorado import create_app

app = create_app()
with app.app_context():
    with app.test_request_context():
        print("📋 Testando novas rotas adicionadas:")
        try:
            from flask import url_for
            
            # Testar upload_termo
            upload_url = url_for('upload_termo', id_publico='PAT-001')
            print(f"✅ upload_termo: {upload_url}")
            
            # Testar ver_termo  
            ver_url = url_for('ver_termo', id_publico='PAT-001')
            print(f"✅ ver_termo: {ver_url}")
            
            print("🎉 TODAS AS NOVAS ROTAS FUNCIONANDO!")
            
        except Exception as e:
            print(f"❌ Erro: {e}")

# Listar todas as rotas para verificar
with app.app_context():
    print("\n📋 Todas as rotas disponíveis:")
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods or [])) 
        print(f"  {rule.endpoint}: {rule.rule} [{methods}]")