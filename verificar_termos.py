"""
Verificar os caminhos dos termos no banco de dados
"""
import psycopg2

def verificar_termos():
    host = "terrano-db.postgres.database.azure.com"
    database = "flexibleserverdb"
    user = "vinicius"
    password = "XFmkbizvA2gL"
    
    try:
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=5432,
            sslmode='require'
        )
        
        cur = conn.cursor()
        
        print("\n📋 Verificando caminhos dos termos no banco...")
        print("="*80)
        
        cur.execute("""
            SELECT id_publico, termo_pdf_path 
            FROM equipamento 
            WHERE termo_pdf_path IS NOT NULL AND termo_pdf_path != 'None'
            ORDER BY id_publico
        """)
        
        termos = cur.fetchall()
        
        if not termos:
            print("\n⚠️  Nenhum termo encontrado no banco!")
        else:
            print(f"\n✅ {len(termos)} equipamentos com termos:\n")
            for id_pub, caminho in termos:
                print(f"  ID: {id_pub}")
                print(f"  Caminho: {caminho}")
                print()
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")

if __name__ == "__main__":
    verificar_termos()
