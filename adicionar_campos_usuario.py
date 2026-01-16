"""
Adicionar campos novos na tabela usuario
"""
import psycopg2

def adicionar_campos_usuario():
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
        
        print("\n🚀 Adicionando campos novos à tabela USUARIO...")
        print("="*60)
        
        # Verificar campos existentes
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'usuario'
        """)
        colunas_existentes = [col[0] for col in cur.fetchall()]
        print(f"\n📊 Colunas atuais em usuario: {colunas_existentes}")
        
        # Novos campos para usuario
        novos_campos = {
            'email': 'VARCHAR(120)',
            'nome_completo': 'VARCHAR(200)',
            'departamento': 'VARCHAR(100)',
            'ativo': 'BOOLEAN',
            'created_at': 'TIMESTAMP',
            'last_login': 'TIMESTAMP'
        }
        
        campos_adicionados = 0
        
        for campo, tipo in novos_campos.items():
            if campo.lower() not in [c.lower() for c in colunas_existentes]:
                print(f"  ➕ Adicionando: {campo} ({tipo})")
                cur.execute(f"ALTER TABLE usuario ADD COLUMN {campo} {tipo}")
                campos_adicionados += 1
            else:
                print(f"  ℹ️  Campo já existe: {campo}")
        
        # Commit
        conn.commit()
        print(f"\n✅ Campos adicionados: {campos_adicionados}")
        print("🎉 Migration de usuario concluída!")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    print("="*60)
    print("MIGRAÇÃO - ADICIONAR CAMPOS NA TABELA USUARIO")
    print("="*60)
    adicionar_campos_usuario()
