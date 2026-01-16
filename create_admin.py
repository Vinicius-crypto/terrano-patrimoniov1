#!/usr/bin/env python3
"""
Script para criar usuário administrador
"""

from app import app, db, Usuario
from werkzeug.security import generate_password_hash

def criar_admin():
    """Cria um usuário administrador padrão"""
    
    with app.app_context():
        # Verificar se admin já existe
        admin_existente = Usuario.query.filter_by(username='admin').first()
        
        if admin_existente:
            print("❌ Usuário admin já existe!")
            return
        
        # Criar novo admin
        admin = Usuario(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            email='admin@terrano.com.br',
            nome_completo='Administrador do Sistema',
            departamento='TI',
            ativo=True,
            nivel_acesso=3  # Administrador
        )
        
        db.session.add(admin)
        
        try:
            db.session.commit()
            print("✅ Usuário admin criado com sucesso!")
            print("👤 Usuário: admin")
            print("🔑 Senha: admin123")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao criar admin: {e}")

if __name__ == '__main__':
    print("=== Criando Usuário Admin ===")
    criar_admin()