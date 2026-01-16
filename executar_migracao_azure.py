"""
Executar migração diretamente no banco Azure PostgreSQL
"""
import psycopg2
from getpass import getpass

def executar_migracao():
    host = "terrano-db.postgres.database.azure.com"
    database = "flexibleserverdb"
    user = "vinicius"
    
    password = getpass("Digite a senha do banco de dados: ")
    
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
        
        print("\n🚀 Iniciando migração...")
        print("="*60)
        
        # Verificar se já existem os campos
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'equipamento'
        """)
        colunas_existentes = [col[0] for col in cur.fetchall()]
        print(f"\n📊 Colunas atuais em equipamento: {len(colunas_existentes)}")
        
        # Lista de novos campos a adicionar
        novos_campos = {
            'valor_residual': 'FLOAT',
            'vida_util_anos': 'INTEGER',
            'valor_depreciado': 'FLOAT',
            'centro_custo': 'VARCHAR(100)',
            'departamento': 'VARCHAR(100)',
            'condicao': 'VARCHAR(50)',
            'proxima_manutencao': 'DATE',
            'garantia_ate': 'DATE',
            'fornecedor_id': 'INTEGER',
            'nota_fiscal': 'VARCHAR(100)',
            'categoria_id': 'INTEGER',
            'subcategoria': 'VARCHAR(100)',
            'tags': 'TEXT',
            'codigo_barras': 'VARCHAR(100)',
            'qr_code': 'TEXT',
            'numero_serie': 'VARCHAR(100)',
            'especificacoes_tecnicas': 'TEXT',
            'capacidade': 'VARCHAR(50)',
            'voltagem': 'VARCHAR(20)',
            'potencia': 'VARCHAR(50)',
            'image_path': 'VARCHAR(500)',
            'image_url': 'TEXT',
            'created_by': 'INTEGER',
            'updated_by': 'INTEGER',
            'created_at': 'TIMESTAMP',
            'updated_at': 'TIMESTAMP',
            'prioridade': 'VARCHAR(20)'
        }
        
        campos_adicionados = 0
        campos_ja_existentes = 0
        
        for campo, tipo in novos_campos.items():
            if campo.lower() not in [c.lower() for c in colunas_existentes]:
                print(f"  ➕ Adicionando: {campo} ({tipo})")
                cur.execute(f"ALTER TABLE equipamento ADD COLUMN {campo} {tipo}")
                campos_adicionados += 1
            else:
                campos_ja_existentes += 1
        
        print(f"\n✅ Campos adicionados: {campos_adicionados}")
        print(f"ℹ️  Campos já existentes: {campos_ja_existentes}")
        
        # Commit das alterações
        conn.commit()
        print("\n🎉 Migração concluída com sucesso!")
        print(f"📊 Total de colunas agora: {len(colunas_existentes) + campos_adicionados}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    print("="*60)
    print("MIGRAÇÃO - ADICIONAR CAMPOS MODERNOS")
    print("="*60)
    executar_migracao()
