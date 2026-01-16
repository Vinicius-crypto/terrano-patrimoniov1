#!/usr/bin/env python3
"""
Script para ativar usuário administrador
"""

import os
import sys

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from models import db, Usuario
import bcrypt

def ativar_admin():
    """Ativa o usuário administrador e reseta a senha"""
    
    with app.app_context():
        # Buscar usuário admin
        admin = Usuario.query.filter_by(username='admin').first()
        
        if not admin:
            print("❌ Usuário admin não encontrado!")
            return False
        
        print(f"👤 Usuário encontrado: {admin.username}")
        print(f"📧 Status atual: {'Ativo' if admin.ativo else 'Inativo'}")
        print(f"🔑 Nível atual: {admin.nivel_acesso}")
        
        # Ativar usuário e resetar senha
        admin.ativo = True
        admin.nivel_acesso = 3  # Garantir que é admin
        
        # Resetar senha para admin123
        password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        admin.password_hash = password_hash
        
        try:
            db.session.commit()
            print("\n✅ Usuário admin ativado com sucesso!")
            print("👤 Usuário: admin")
            print("🔑 Senha: admin123")
            print("🎯 Nível: 3 (Administrador)")
            print("📧 Status: Ativo")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao ativar admin: {e}")
            return False

if __name__ == '__main__':
    print("=== Ativando Usuário Admin ===")
    if ativar_admin():
        print("\n🎉 Agora você pode fazer login com:")
        print("   Usuário: admin")
        print("   Senha: admin123")
        print("   E verá o link '🔑 Admin' no menu superior!")
    else:
        print("\n❌ Falha ao ativar usuário admin")