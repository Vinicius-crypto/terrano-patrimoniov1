"""
Script para verificar os usuários cadastrados no banco de dados
"""
import psycopg2
from getpass import getpass

def verificar_usuarios():
    # Conexão com o banco Azure PostgreSQL
    host = "terrano-db.postgres.database.azure.com"
    database = "flexibleserverdb"
    user = "adminvini"
    
    # Solicita a senha
    password = getpass("Digite a senha do banco de dados: ")
    
    try:
        # Conectar ao banco
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=5432,
            sslmode='require'
        )
        
        cur = conn.cursor()
        
        # Buscar todos os usuários
        print("\n" + "="*80)
        print("USUÁRIOS CADASTRADOS")
        print("="*80)
        
        cur.execute("""
            SELECT id, username, nivel_acesso, email, nome_completo, departamento, ativo
            FROM usuario
            ORDER BY nivel_acesso DESC, username
        """)
        
        usuarios = cur.fetchall()
        
        print(f"\nTotal de usuários: {len(usuarios)}\n")
        
        for usuario in usuarios:
            id_user, username, nivel, email, nome, depto, ativo = usuario
            nivel_texto = {1: "Usuário", 2: "Gerente", 3: "Administrador"}.get(nivel, f"Nível {nivel}")
            status = "✅ Ativo" if ativo else "❌ Inativo"
            
            print(f"ID: {id_user}")
            print(f"Username: {username}")
            print(f"Nível de Acesso: {nivel} - {nivel_texto}")
            print(f"Email: {email or 'N/A'}")
            print(f"Nome: {nome or 'N/A'}")
            print(f"Departamento: {depto or 'N/A'}")
            print(f"Status: {status}")
            print("-" * 80)
        
        cur.close()
        conn.close()
        
        print("\n✅ Verificação concluída!")
        
    except Exception as e:
        print(f"\n❌ Erro ao conectar: {e}")

if __name__ == "__main__":
    verificar_usuarios()
