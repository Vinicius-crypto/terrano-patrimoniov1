"""
Criar tabelas de Categoria e Fornecedor no PostgreSQL
"""
import psycopg2

def criar_tabelas():
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
        
        conn.autocommit = False
        cur = conn.cursor()
        
        print("\n🚀 Criando tabelas de Categoria e Fornecedor...")
        print("="*60)
        
        # Criar tabela categoria
        print("\n📊 Criando tabela CATEGORIA...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS categoria (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL UNIQUE,
                icone VARCHAR(50),
                cor VARCHAR(7),
                descricao TEXT,
                ativo BOOLEAN DEFAULT TRUE
            )
        """)
        print("✅ Tabela categoria criada/verificada")
        
        # Criar tabela fornecedor
        print("\n🏢 Criando tabela FORNECEDOR...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fornecedor (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(200) NOT NULL,
                cnpj VARCHAR(18),
                email VARCHAR(120),
                telefone VARCHAR(20),
                endereco TEXT,
                ativo BOOLEAN DEFAULT TRUE
            )
        """)
        print("✅ Tabela fornecedor criada/verificada")
        
        # Inserir categorias padrão
        print("\n📝 Inserindo categorias padrão...")
        categorias_padrao = [
            ('Informática', 'Equipamentos de TI e Computadores'),
            ('Escritório', 'Móveis e equipamentos de escritório'),
            ('Telefonia', 'Telefones e equipamentos de comunicação'),
            ('Segurança', 'Câmeras e sistemas de segurança'),
            ('Rede', 'Roteadores, switches e equipamentos de rede')
        ]
        
        for nome, descricao in categorias_padrao:
            cur.execute("""
                INSERT INTO categoria (nome, descricao, ativo)
                VALUES (%s, %s, TRUE)
                ON CONFLICT (nome) DO NOTHING
            """, (nome, descricao))
        
        conn.commit()
        print("\n🎉 Tabelas criadas com sucesso!")
        print("✅ Categorias padrão inseridas")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    print("="*60)
    print("CRIAR TABELAS CATEGORIA E FORNECEDOR")
    print("="*60)
    criar_tabelas()
