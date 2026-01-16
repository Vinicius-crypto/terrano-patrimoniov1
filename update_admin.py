#!/usr/bin/env python3
"""Atualizar o usuário admin com nome completo"""

from app import app, db, Usuario

def atualizar_admin():
    """Atualizar admin com nome completo"""
    with app.app_context():
        admin = Usuario.query.filter_by(username='admin').first()
        if admin:
            if not admin.nome_completo:
                admin.nome_completo = 'Administrador do Sistema'
                db.session.commit()
                print(f"✅ Admin atualizado: {admin.username} - {admin.nome_completo}")
            else:
                print(f"✅ Admin já tem nome: {admin.nome_completo}")
        else:
            print("❌ Admin não encontrado")

if __name__ == "__main__":
    atualizar_admin()