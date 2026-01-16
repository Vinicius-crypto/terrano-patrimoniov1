#!/usr/bin/env python3
"""
Script para criar usuário administrador diretamente
"""

import os
import sys

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, Usuario
import bcrypt

def criar_admin():
    """Cria um usuário administrador padrão"""
    
    with app.app_context():
        # Verificar se admin já existe
        admin_existente = Usuario.query.filter_by(username='admin').first()
        
        if admin_existente:
            print("❌ Usuário admin já existe!")
            print(f"👤 Usuário: {admin_existente.username}")
            print(f"🔑 Nível: {admin_existente.nivel_acesso}")
            print(f"📧 Status: {'Ativo' if admin_existente.ativo else 'Inativo'}")
            return admin_existente
        
        # Criar hash da senha
        password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Criar novo admin
        admin = Usuario(
            username='admin',
            password_hash=password_hash,
            nome_completo='Administrador do Sistema',
            ativo=True,
            nivel_acesso=3  # Administrador
        )
        
        db.session.add(admin)
        
        try:
            db.session.commit()
            print("✅ Usuário admin criado com sucesso!")
            print("👤 Usuário: admin")
            print("🔑 Senha: admin123")
            print("🎯 Nível: 3 (Administrador)")
            return admin
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao criar admin: {e}")
            return None

if __name__ == '__main__':
    print("=== Criando Usuário Admin ===")
    admin = criar_admin()
    if admin:
        print("\n🎉 Agora você pode fazer login com:")
        print("   Usuário: admin")
        print("   Senha: admin123")