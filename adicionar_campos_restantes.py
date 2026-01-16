"""
Adicionar campos restantes na tabela equipamento
"""
import psycopg2

def adicionar_campos_restantes():
    host = "terrano-db.postgres.database.azure.com"
    database = "flexibleserverdb"
    user = "vinicius"
    password = "XFmkbizvA2gL"
    
    try:
        print(f"\n🔌 Conectando ao banco Azure PostgreSQL...")
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=5432,
            sslmode='require'
        )
        
        conn.autocommit = False
        cur = conn.cursor()
        
        print("\n🚀 Adicionando campos restantes à tabela EQUIPAMENTO...")
        print("="*60)
        
        # Campos faltantes do modelo SQLAlchemy
        campos_faltantes = {
            'rfid_tag': 'VARCHAR(100)',
            'imagem_url': 'TEXT',
            'termo_pdf_path': 'VARCHAR(500)',
            'manual_url': 'TEXT',
            'SPE': 'VARCHAR(100)',
            'observacoes': 'TEXT',
            'especificacoes_tecnicas': 'TEXT',
            'configuracao': 'TEXT',
            'created_at': 'TIMESTAMP',
            'updated_at': 'TIMESTAMP',
            'created_by': 'INTEGER',
            'updated_by': 'INTEGER',
            'ativo': 'BOOLEAN',
            'bloqueado': 'BOOLEAN',
            'motivo_bloqueio': 'TEXT'
        }
        
        # Verificar quais já existem
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'equipamento'
        """)
        colunas_existentes = [col[0].lower() for col in cur.fetchall()]
        
        campos_adicionados = 0
        
        for campo, tipo in campos_faltantes.items():
            if campo.lower() not in colunas_existentes:
                print(f"  ➕ Adicionando: {campo} ({tipo})")
                try:
                    cur.execute(f'ALTER TABLE equipamento ADD COLUMN "{campo}" {tipo}')
                    campos_adicionados += 1
                except Exception as e:
                    print(f"     ⚠️  Erro ao adicionar {campo}: {e}")
            else:
                print(f"  ℹ️  Campo já existe: {campo}")
        
        conn.commit()
        print(f"\n✅ Campos adicionados: {campos_adicionados}")
        print("🎉 Migration concluída!")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    print("="*60)
    print("MIGRAÇÃO - ADICIONAR CAMPOS RESTANTES")
    print("="*60)
    adicionar_campos_restantes()
