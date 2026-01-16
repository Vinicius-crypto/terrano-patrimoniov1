"""
Script Interativo para Analisar Banco de Dados Azure PostgreSQL
Execute e informe suas credenciais
"""
import psycopg2
import getpass

print("="*70)
print("CONECTAR AO BANCO DE DADOS POSTGRESQL NO AZURE")
print("="*70)
print()

# Configuração
HOST = 'terrano-db.postgres.database.azure.com'
DATABASE = 'flexibleserverdb'
PORT = 5432

print(f"Host: {HOST}")
print(f"Database: {DATABASE}")
print(f"Port: {PORT}")
print()

# Solicitar credenciais
usuario = input("Usuário PostgreSQL (ex: admin@terrano-db): ")
senha = getpass.getpass("Senha: ")

try:
    # Conectar
    print("\n🔌 Conectando...")
    conn = psycopg2.connect(
        host=HOST,
        database=DATABASE,
        user=usuario,
        password=senha,
        port=PORT,
        sslmode='require'
    )
    
    cursor = conn.cursor()
    print("✅ Conectado com sucesso!\n")
    
    # Listar tabelas
    print("="*70)
    print("TABELAS NO SCHEMA PUBLIC")
    print("="*70)
    
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    
    tabelas = [row[0] for row in cursor.fetchall()]
    
    if not tabelas:
        print("❌ Nenhuma tabela encontrada!")
    else:
        print(f"\n✅ Encontradas {len(tabelas)} tabelas:")
        for i, tabela in enumerate(tabelas, 1):
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
            count = cursor.fetchone()[0]
            print(f"   {i}. {tabela} ({count} registros)")
        
        print("\n" + "="*70)
        
        # Analisar cada tabela
        for tabela in tabelas:
            print(f"\n📊 TABELA: {tabela.upper()}")
            print("-"*70)
            
            # Contar registros
            cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
            count = cursor.fetchone()[0]
            print(f"📈 Total de registros: {count}\n")
            
            # Estrutura da tabela
            cursor.execute(f"""
                SELECT 
                    column_name,
                    data_type,
                    character_maximum_length,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = '{tabela}'
                ORDER BY ordinal_position;
            """)
            
            colunas = cursor.fetchall()
            
            print("ESTRUTURA:")
            for col in colunas:
                col_name, data_type, max_len, nullable, default = col
                
                # Tipo com tamanho
                if max_len:
                    tipo = f"{data_type}({max_len})"
                else:
                    tipo = data_type
                
                # Nullable
                null_str = "NULL" if nullable == "YES" else "NOT NULL"
                
                # Default simplificado
                if default:
                    if len(str(default)) > 40:
                        default_str = f"DEFAULT {str(default)[:37]}..."
                    else:
                        default_str = f"DEFAULT {default}"
                else:
                    default_str = ""
                
                print(f"   • {col_name:30s} {tipo:20s} {null_str:10s} {default_str}")
            
            # Constraints
            cursor.execute(f"""
                SELECT
                    tc.constraint_type,
                    kcu.column_name,
                    ccu.table_name AS foreign_table,
                    ccu.column_name AS foreign_column
                FROM information_schema.table_constraints AS tc
                LEFT JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                LEFT JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.table_schema = 'public'
                AND tc.table_name = '{tabela}';
            """)
            
            constraints = cursor.fetchall()
            if constraints:
                print("\nCONSTRAINTS:")
                for cons in constraints:
                    cons_type, col, fk_table, fk_col = cons
                    if cons_type == 'PRIMARY KEY':
                        print(f"   🔑 PRIMARY KEY: {col}")
                    elif cons_type == 'FOREIGN KEY':
                        print(f"   🔗 FOREIGN KEY: {col} → {fk_table}.{fk_col}")
                    elif cons_type == 'UNIQUE':
                        print(f"   ✨ UNIQUE: {col}")
            
            print()
        
        # Verificar se estrutura é compatível com models.py
        print("="*70)
        print("ANÁLISE DE COMPATIBILIDADE")
        print("="*70)
        
        tabelas_esperadas = ['usuario', 'equipamento', 'categoria', 'fornecedor', 
                           'historico_equipamento', 'notificacao', 'manutencao_programada']
        
        print("\n✅ Tabelas presentes no Azure:")
        for t in tabelas:
            status = "✅" if t in tabelas_esperadas else "⚠️ "
            print(f"   {status} {t}")
        
        print("\n📋 Tabelas esperadas em models.py:")
        for t in tabelas_esperadas:
            status = "✅" if t in tabelas else "❌"
            print(f"   {status} {t}")
        
        # Verificar tabela equipamento em detalhes (a mais importante)
        if 'equipamento' in tabelas:
            print("\n" + "="*70)
            print("VERIFICAÇÃO DETALHADA: TABELA EQUIPAMENTO")
            print("="*70)
            
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'equipamento'
                ORDER BY ordinal_position;
            """)
            
            colunas_atual = [row[0] for row in cursor.fetchall()]
            
            # Campos esperados em models.py
            campos_esperados = [
                'id_interno', 'id_publico', 'tipo', 'marca', 'modelo', 'num_serie',
                'data_aquisicao', 'valor', 'valor_residual', 'vida_util_anos',
                'valor_depreciado', 'localizacao', 'responsavel', 'centro_custo',
                'departamento', 'status', 'condicao', 'ultima_manutencao',
                'proxima_manutencao', 'garantia_ate', 'fornecedor_id', 'nota_fiscal',
                'categoria_id', 'subcategoria', 'tags', 'codigo_barras', 'qr_code',
                'rfid_tag', 'imagem_url', 'termo_pdf_path', 'manual_url', 'spe',
                'observacoes', 'especificacoes_tecnicas', 'configuracao',
                'created_at', 'updated_at', 'created_by', 'updated_by',
                'ativo', 'bloqueado', 'motivo_bloqueio'
            ]
            
            print(f"\n📊 Campos no Azure: {len(colunas_atual)}")
            print(f"📋 Campos em models.py: {len(campos_esperados)}")
            
            # Campos que faltam no Azure
            faltando = [c for c in campos_esperados if c.lower() not in [col.lower() for col in colunas_atual]]
            if faltando:
                print(f"\n❌ Campos que FALTAM no Azure ({len(faltando)}):")
                for campo in faltando:
                    print(f"   • {campo}")
            
            # Campos extras no Azure
            extras = [c for c in colunas_atual if c.lower() not in [col.lower() for col in campos_esperados]]
            if extras:
                print(f"\n⚠️  Campos EXTRAS no Azure ({len(extras)}):")
                for campo in extras:
                    print(f"   • {campo}")
            
            if not faltando and not extras:
                print("\n✅ ESTRUTURA 100% COMPATÍVEL!")
            else:
                print("\n⚠️  ESTRUTURA DIFERENTE - MIGRAÇÃO NECESSÁRIA!")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*70)
    print("✅ Análise concluída!")
    print("="*70)

except psycopg2.Error as e:
    print(f"\n❌ Erro de banco de dados: {e}")
except Exception as e:
    print(f"\n❌ Erro: {e}")
