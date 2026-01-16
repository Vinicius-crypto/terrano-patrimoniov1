"""
Script para fazer backup do banco de dados antes da migração
"""
import psycopg2
from datetime import datetime
from getpass import getpass
import json

def fazer_backup():
    host = "terrano-db.postgres.database.azure.com"
    database = "flexibleserverdb"
    user = "vinicius"
    
    password = getpass("Digite a senha do banco de dados: ")
    
    try:
        print(f"\n🔌 Conectando ao banco de dados...")
        print(f"   Host: {host}")
        print(f"   Database: {database}")
        print(f"   User: {user}")
        
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=5432,
            sslmode='require'
        )
    except Exception as parse_error:
        print(f"❌ Erro ao conectar: {parse_error}")
        return
    
    try:
        
        cur = conn.cursor()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Backup dos equipamentos
        print("\n📦 Fazendo backup dos EQUIPAMENTOS...")
        cur.execute("SELECT * FROM equipamento ORDER BY id_publico")
        equipamentos = cur.fetchall()
        
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'equipamento' 
            ORDER BY ordinal_position
        """)
        colunas_equipamento = [col[0] for col in cur.fetchall()]
        
        equipamentos_dict = [dict(zip(colunas_equipamento, eq)) for eq in equipamentos]
        
        # Backup dos usuários
        print("👥 Fazendo backup dos USUÁRIOS...")
        cur.execute("SELECT * FROM usuario ORDER BY username")
        usuarios = cur.fetchall()
        
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'usuario' 
            ORDER BY ordinal_position
        """)
        colunas_usuario = [col[0] for col in cur.fetchall()]
        
        usuarios_dict = [dict(zip(colunas_usuario, usr)) for usr in usuarios]
        
        # Salvar backup
        backup_data = {
            'timestamp': timestamp,
            'database': database,
            'equipamentos': {
                'total': len(equipamentos_dict),
                'colunas': colunas_equipamento,
                'dados': equipamentos_dict
            },
            'usuarios': {
                'total': len(usuarios_dict),
                'colunas': colunas_usuario,
                'dados': usuarios_dict
            }
        }
        
        filename = f"backup_antes_migracao_{timestamp}.json"
        
        # Converter datetime para string
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return str(obj)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2, default=json_serializer)
        
        print(f"\n✅ Backup salvo com sucesso: {filename}")
        print(f"   📊 {len(equipamentos_dict)} equipamentos")
        print(f"   👥 {len(usuarios_dict)} usuários")
        
        # Criar script SQL de restore
        sql_filename = f"restore_backup_{timestamp}.sql"
        with open(sql_filename, 'w', encoding='utf-8') as f:
            f.write("-- Script de Restore do Backup\n")
            f.write(f"-- Gerado em: {timestamp}\n\n")
            
            f.write("-- EQUIPAMENTOS\n")
            for eq in equipamentos_dict:
                colunas = ', '.join(eq.keys())
                valores = ', '.join([f"'{v}'" if v is not None else 'NULL' for v in eq.values()])
                f.write(f"INSERT INTO equipamento ({colunas}) VALUES ({valores});\n")
            
            f.write("\n-- USUÁRIOS\n")
            for usr in usuarios_dict:
                colunas = ', '.join(usr.keys())
                valores = ', '.join([f"'{v}'" if v is not None else 'NULL' for v in usr.values()])
                f.write(f"INSERT INTO usuario ({colunas}) VALUES ({valores});\n")
        
        print(f"   📝 Script SQL: {sql_filename}")
        
        cur.close()
        conn.close()
        
        print("\n🎉 Backup completo!")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")

if __name__ == "__main__":
    print("="*60)
    print("BACKUP DO BANCO DE DADOS ANTES DA MIGRAÇÃO")
    print("="*60)
    fazer_backup()
