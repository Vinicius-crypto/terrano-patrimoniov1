import pandas as pd
from sqlalchemy import create_engine

# Caminho para o banco SQLite local
sqlite_engine = create_engine(r'sqlite:///C:\Users\Vinicius\Projetos\Terrano-patrimonio\patrimonio.db')

# Conexão com o PostgreSQL do Azure
postgres_engine = create_engine('postgresql+psycopg2://vinicius:XFmkbizvA2gL@terrano-db.postgres.database.azure.com:5432/flexibleserverdb')

# Leitura da tabela
df = pd.read_sql_query('SELECT * FROM equipamentos', con=sqlite_engine)

# Corrigir datas
for col in ['data_aquisicao', 'ultima_manutencao']:
    if col in df.columns:
        df[col] = df[col].replace('01-01-1900', None)
        df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)

# Truncar campos que têm limitação no banco de dados
def truncate_column(df, col, max_len):
    if col in df.columns:
        df[col] = df[col].astype(str).str.slice(0, max_len)

truncate_column(df, 'tipo', 100)
truncate_column(df, 'marca', 100)
truncate_column(df, 'modelo', 100)
truncate_column(df, 'num_serie', 100)
truncate_column(df, 'localizacao', 200)
truncate_column(df, 'status', 50)
truncate_column(df, 'responsavel', 100)
truncate_column(df, 'SPE', 50)
truncate_column(df, 'termo_pdf_path', 500)

# Exportar para o PostgreSQL
df.to_sql('equipamento', con=postgres_engine, if_exists='append', index=False)

print("✅ Dados migrados com sucesso!")
