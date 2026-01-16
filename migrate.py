#!/usr/bin/env python3
"""
Script de migração segura para adicionar novos campos ao modelo Equipamento
Execute este script para aplicar as alterações no banco de dados de forma segura
"""

import os
import sys
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Adicionar o diretório pai ao path para importar a aplicação
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_migration():
    """Executa a migração do banco de dados"""
    
    print("🚀 Iniciando processo de migração...")
    
    # Verificar se temos backup
    backup_confirmation = input("⚠️  Você fez backup do banco de dados? (s/N): ")
    if backup_confirmation.lower() not in ['s', 'sim', 'y', 'yes']:
        print("❌ Por favor, faça um backup antes de continuar!")
        print("   Para PostgreSQL: pg_dump $DATABASE_URL > backup.sql")
        print("   Para SQLite: cp database.db database_backup.db")
        return False
    
    try:
        # Importar a aplicação
        from app import app, db
        
        with app.app_context():
            print("📋 Gerando arquivos de migração...")
            
            # Gerar migração
            os.system('flask db migrate -m "Add enhanced fields to Equipamento model - codigo_barras, garantia_ate, centro_custo, categoria, audit fields"')
            
            # Confirmação para aplicar
            apply_confirmation = input("✅ Migração gerada! Aplicar ao banco? (s/N): ")
            if apply_confirmation.lower() in ['s', 'sim', 'y', 'yes']:
                print("🔄 Aplicando migração...")
                os.system('flask db upgrade')
                
                print("✅ Migração aplicada com sucesso!")
                print("📊 Atualizando dados existentes...")
                
                # Atualizar dados existentes com valores padrão
                equipamentos = db.session.execute(db.text("SELECT id_interno FROM equipamento")).fetchall()
                count = 0
                
                for equipamento in equipamentos:
                    # Adicionar timestamps aos registros existentes que não têm
                    db.session.execute(
                        db.text("""
                            UPDATE equipamento 
                            SET created_at = COALESCE(created_at, :now),
                                updated_at = COALESCE(updated_at, :now),
                                vida_util_anos = COALESCE(vida_util_anos, 5),
                                valor_residual = COALESCE(valor_residual, 0.0)
                            WHERE id_interno = :id
                        """),
                        {"now": datetime.utcnow(), "id": equipamento[0]}
                    )
                    count += 1
                
                db.session.commit()
                print(f"📈 {count} registros atualizados com valores padrão")
                
                print("🎉 Processo de migração concluído!")
                print("💡 Novos campos disponíveis:")
                print("   - Código de Barras")
                print("   - Data de Garantia")  
                print("   - Centro de Custo")
                print("   - Fornecedor")
                print("   - Categoria/Subcategoria")
                print("   - Vida Útil (anos)")
                print("   - Campos de Auditoria (created_at, updated_at, etc.)")
                
                return True
            else:
                print("❌ Migração cancelada pelo usuário")
                return False
                
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        print("🔄 Execute 'flask db downgrade' para reverter se necessário")
        return False

def check_migration_status():
    """Verifica o status atual das migrações"""
    print("📋 Status das migrações:")
    os.system('flask db current')
    print("\n📜 Histórico de migrações:")
    os.system('flask db history')

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 SISTEMA DE MIGRAÇÃO - TERRANO PATRIMÔNIO v1")
    print("=" * 60)
    
    action = input("Escolha uma ação:\n1. Ver status das migrações\n2. Executar migração\n3. Sair\n> ")
    
    if action == "1":
        check_migration_status()
    elif action == "2":
        run_migration()
    else:
        print("👋 Saindo...")