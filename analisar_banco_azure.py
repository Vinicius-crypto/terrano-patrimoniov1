#!/usr/bin/env python3
"""
Script para Analisar Estrutura do Banco de Dados PostgreSQL no Azure
Conecta ao banco e extrai toda a estrutura de tabelas, colunas, constraints
"""
import psycopg2
from psycopg2 import sql
import json
from datetime import datetime

# Configurações do banco de dados Azure
DB_CONFIG = {
    'host': 'terrano-db.postgres.database.azure.com',
    'database': 'flexibleserverdb',
    'user': '',  # PREENCHER
    'password': '',  # PREENCHER
    'port': 5432,
    'sslmode': 'require'
}

def conectar_banco():
    """Conectar ao banco PostgreSQL no Azure"""
    print("🔌 Conectando ao banco de dados Azure PostgreSQL...")
    print(f"   Host: {DB_CONFIG['host']}")
    print(f"   Database: {DB_CONFIG['database']}")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Conexão estabelecida com sucesso!\n")
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return None

def obter_tabelas(cursor):
    """Obter lista de todas as tabelas no schema public"""
    query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """
    cursor.execute(query)
    return [row[0] for row in cursor.fetchall()]

def obter_colunas(cursor, tabela):
    """Obter todas as colunas de uma tabela"""
    query = """
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = %s
        ORDER BY ordinal_position;
    """
    cursor.execute(query, (tabela,))
    return cursor.fetchall()

def obter_constraints(cursor, tabela):
    """Obter constraints de uma tabela"""
    query = """
        SELECT
            tc.constraint_name,
            tc.constraint_type,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        LEFT JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        LEFT JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.table_schema = 'public'
        AND tc.table_name = %s;
    """
    cursor.execute(query, (tabela,))
    return cursor.fetchall()

def obter_indices(cursor, tabela):
    """Obter índices de uma tabela"""
    query = """
        SELECT
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND tablename = %s;
    """
    cursor.execute(query, (tabela,))
    return cursor.fetchall()

def contar_registros(cursor, tabela):
    """Contar número de registros em uma tabela"""
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {tabela};")
        return cursor.fetchone()[0]
    except:
        return 0

def analisar_estrutura():
    """Análise completa da estrutura do banco de dados"""
    
    # Verificar se credenciais foram preenchidas
    if not DB_CONFIG['user'] or not DB_CONFIG['password']:
        print("❌ ERRO: Preencha as credenciais no script!")
        print("\nEdite o arquivo e preencha:")
        print("  DB_CONFIG['user'] = 'seu_usuario@terrano-db'")
        print("  DB_CONFIG['password'] = 'sua_senha'")
        return
    
    conn = conectar_banco()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # Obter lista de tabelas
    print("📋 Analisando tabelas no banco de dados...\n")
    tabelas = obter_tabelas(cursor)
    
    if not tabelas:
        print("⚠️  Nenhuma tabela encontrada no schema public")
        return
    
    print(f"✅ Encontradas {len(tabelas)} tabelas:\n")
    
    estrutura_completa = {}
    
    for tabela in tabelas:
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"📊 TABELA: {tabela}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # Contar registros
        count = contar_registros(cursor, tabela)
        print(f"   📈 Registros: {count}")
        print()
        
        # Colunas
        print("   📋 COLUNAS:")
        colunas = obter_colunas(cursor, tabela)
        colunas_info = []
        
        for col in colunas:
            col_name, data_type, max_length, nullable, default = col
            
            # Formatar tipo
            if max_length:
                tipo_completo = f"{data_type}({max_length})"
            else:
                tipo_completo = data_type
            
            # Nullable
            null_str = "NULL" if nullable == "YES" else "NOT NULL"
            
            # Default
            default_str = f"DEFAULT {default}" if default else ""
            
            linha = f"      • {col_name}: {tipo_completo} {null_str} {default_str}".strip()
            print(linha)
            
            colunas_info.append({
                'name': col_name,
                'type': data_type,
                'max_length': max_length,
                'nullable': nullable,
                'default': default
            })
        
        print()
        
        # Constraints
        print("   🔒 CONSTRAINTS:")
        constraints = obter_constraints(cursor, tabela)
        constraints_info = []
        
        constraint_dict = {}
        for cons in constraints:
            cons_name, cons_type, col_name, fk_table, fk_col = cons
            
            if cons_name not in constraint_dict:
                constraint_dict[cons_name] = {
                    'type': cons_type,
                    'columns': [],
                    'fk_table': fk_table,
                    'fk_column': fk_col
                }
            constraint_dict[cons_name]['columns'].append(col_name)
        
        for cons_name, cons_info in constraint_dict.items():
            cons_type = cons_info['type']
            cols = ', '.join(cons_info['columns'])
            
            if cons_type == 'PRIMARY KEY':
                print(f"      🔑 PRIMARY KEY: {cols}")
            elif cons_type == 'FOREIGN KEY':
                print(f"      🔗 FOREIGN KEY: {cols} → {cons_info['fk_table']}.{cons_info['fk_column']}")
            elif cons_type == 'UNIQUE':
                print(f"      ✨ UNIQUE: {cols}")
            elif cons_type == 'CHECK':
                print(f"      ✓ CHECK: {cons_name}")
            
            constraints_info.append(cons_info)
        
        if not constraints:
            print("      (nenhuma constraint)")
        
        print()
        
        # Índices
        print("   📑 ÍNDICES:")
        indices = obter_indices(cursor, tabela)
        indices_info = []
        
        for idx in indices:
            idx_name, idx_def = idx
            print(f"      • {idx_name}")
            indices_info.append({'name': idx_name, 'definition': idx_def})
        
        if not indices:
            print("      (nenhum índice)")
        
        print()
        
        estrutura_completa[tabela] = {
            'record_count': count,
            'columns': colunas_info,
            'constraints': constraints_info,
            'indices': indices_info
        }
    
    # Salvar estrutura em arquivo JSON
    output_file = f"estrutura_banco_azure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(estrutura_completa, f, indent=2, ensure_ascii=False, default=str)
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"✅ Análise completa!")
    print(f"📄 Estrutura salva em: {output_file}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Resumo
    print("\n📊 RESUMO:")
    print(f"   • Total de tabelas: {len(tabelas)}")
    total_registros = sum(estrutura_completa[t]['record_count'] for t in tabelas)
    print(f"   • Total de registros: {total_registros}")
    print(f"   • Tabelas: {', '.join(tabelas)}")
    
    cursor.close()
    conn.close()

def gerar_comparacao_com_models():
    """Comparar estrutura do banco com models.py"""
    print("\n" + "="*60)
    print("COMPARAÇÃO COM MODELS.PY")
    print("="*60 + "\n")
    
    # Tabelas esperadas em models.py
    tabelas_esperadas = {
        'usuario': [
            'id', 'username', 'password_hash', 'nivel_acesso', 'email',
            'nome_completo', 'departamento', 'ativo', 'created_at', 'last_login'
        ],
        'equipamento': [
            'id_interno', 'id_publico', 'tipo', 'marca', 'modelo', 'num_serie',
            'data_aquisicao', 'valor', 'valor_residual', 'vida_util_anos',
            'valor_depreciado', 'localizacao', 'responsavel', 'centro_custo',
            'departamento', 'status', 'condicao', 'ultima_manutencao',
            'proxima_manutencao', 'garantia_ate', 'fornecedor_id', 'nota_fiscal',
            'categoria_id', 'subcategoria', 'tags', 'codigo_barras', 'qr_code',
            'rfid_tag', 'imagem_url', 'termo_pdf_path', 'manual_url', 'SPE',
            'observacoes', 'especificacoes_tecnicas', 'configuracao',
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'ativo', 'bloqueado', 'motivo_bloqueio'
        ],
        'categoria': [
            'id', 'nome', 'icone', 'cor', 'descricao', 'ativo'
        ],
        'fornecedor': [
            'id', 'nome', 'cnpj', 'email', 'telefone', 'endereco',
            'contato_principal', 'observacoes', 'ativo', 'created_at'
        ],
        'historico_equipamento': [
            'id', 'equipamento_id', 'acao', 'campo_alterado', 'valor_anterior',
            'valor_novo', 'descricao', 'data_acao', 'usuario_id', 'ip_address'
        ],
        'notificacao': [
            'id', 'usuario_id', 'titulo', 'mensagem', 'tipo', 'lida',
            'link_acao', 'equipamento_id', 'created_at', 'lida_em'
        ],
        'manutencao_programada': [
            'id', 'equipamento_id', 'tipo', 'descricao', 'data_programada',
            'data_realizada', 'responsavel_tecnico', 'custo_estimado',
            'custo_real', 'status', 'observacoes', 'created_at', 'created_by'
        ]
    }
    
    print("Tabelas esperadas em models.py:")
    for tabela, colunas in tabelas_esperadas.items():
        print(f"\n  📊 {tabela}:")
        print(f"     Colunas esperadas: {len(colunas)}")
        print(f"     Campos: {', '.join(colunas[:5])}..." if len(colunas) > 5 else f"     Campos: {', '.join(colunas)}")
    
    print("\n⚠️  IMPORTANTE:")
    print("Execute este script para comparar com sua estrutura real no Azure!")

if __name__ == '__main__':
    print("="*60)
    print("ANÁLISE DE ESTRUTURA DO BANCO DE DADOS AZURE")
    print("Sistema: Terrano Patrimônio v1")
    print("="*60)
    print()
    
    # Solicitar credenciais se não preenchidas
    if not DB_CONFIG['user']:
        print("⚠️  ATENÇÃO: Configure as credenciais antes de executar!")
        print("\nEdite este arquivo e preencha:")
        print("  DB_CONFIG['user'] = 'seu_usuario@terrano-db'")
        print("  DB_CONFIG['password'] = 'sua_senha'")
        print("\nOu informe agora:")
        user = input("\nUsuário PostgreSQL: ").strip()
        password = input("Senha: ").strip()
        
        if user and password:
            DB_CONFIG['user'] = user
            DB_CONFIG['password'] = password
        else:
            print("\n❌ Credenciais não fornecidas. Abortando.")
            gerar_comparacao_com_models()
            exit(1)
    
    analisar_estrutura()
    gerar_comparacao_com_models()
