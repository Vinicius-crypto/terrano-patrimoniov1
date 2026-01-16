#!/usr/bin/env python3
"""
Script para inicializar dados padrão no banco de dados
"""

from app import app, db, Categoria, Fornecedor

def inicializar_dados_padrao():
    """Inicializa categorias e fornecedores padrão no banco de dados"""
    
    with app.app_context():
        # Criar tabelas se não existirem
        db.create_all()
        
        # Categorias padrão
        categorias_padrao = [
            {'nome': 'Informática', 'descricao': 'Equipamentos de informática e tecnologia'},
            {'nome': 'Mobiliário', 'descricao': 'Móveis e equipamentos de escritório'},
            {'nome': 'Eletrodomésticos', 'descricao': 'Aparelhos eletrodomésticos'},
            {'nome': 'Ferramentas', 'descricao': 'Ferramentas e equipamentos de trabalho'},
            {'nome': 'Veículos', 'descricao': 'Veículos e equipamentos de transporte'},
            {'nome': 'Equipamentos Médicos', 'descricao': 'Equipamentos hospitalares e médicos'},
            {'nome': 'Equipamentos de Segurança', 'descricao': 'Equipamentos de segurança e proteção'},
            {'nome': 'Equipamentos de Comunicação', 'descricao': 'Equipamentos de telecomunicações'},
            {'nome': 'Equipamentos Industriais', 'descricao': 'Máquinas e equipamentos industriais'},
            {'nome': 'Outros', 'descricao': 'Outros tipos de equipamentos'}
        ]
        
        print("Criando categorias padrão...")
        for cat_data in categorias_padrao:
            categoria_existente = Categoria.query.filter_by(nome=cat_data['nome']).first()
            if not categoria_existente:
                categoria = Categoria(nome=cat_data['nome'], descricao=cat_data['descricao'])
                db.session.add(categoria)
                print(f"✓ Categoria criada: {cat_data['nome']}")
            else:
                print(f"- Categoria já existe: {cat_data['nome']}")
        
        # Fornecedores padrão
        fornecedores_padrao = [
            {
                'nome': 'Dell Technologies',
                'cnpj': '00.000.000/0001-00',
                'email': 'vendas@dell.com.br',
                'contato_principal': 'João Silva',
                'telefone': '(11) 1234-5678',
                'endereco': 'São Paulo, SP'
            },
            {
                'nome': 'HP Inc.',
                'cnpj': '00.000.000/0001-01',
                'email': 'contato@hp.com.br',
                'contato_principal': 'Maria Santos',
                'telefone': '(21) 9876-5432',
                'endereco': 'Rio de Janeiro, RJ'
            },
            {
                'nome': 'Lenovo Brasil',
                'cnpj': '00.000.000/0001-02',
                'email': 'vendas@lenovo.com.br',
                'contato_principal': 'Carlos Oliveira',
                'telefone': '(31) 5555-1234',
                'endereco': 'Belo Horizonte, MG'
            },
            {
                'nome': 'Microsoft Corporation',
                'cnpj': '00.000.000/0001-03',
                'email': 'suporte@microsoft.com.br',
                'contato_principal': 'Ana Costa',
                'telefone': '(61) 7777-9999',
                'endereco': 'Brasília, DF'
            },
            {
                'nome': 'Samsung Electronics',
                'cnpj': '00.000.000/0001-04',
                'email': 'contato@samsung.com.br',
                'contato_principal': 'Roberto Lima',
                'telefone': '(41) 3333-2222',
                'endereco': 'Curitiba, PR'
            }
        ]
        
        print("\nCriando fornecedores padrão...")
        for forn_data in fornecedores_padrao:
            fornecedor_existente = Fornecedor.query.filter_by(cnpj=forn_data['cnpj']).first()
            if not fornecedor_existente:
                fornecedor = Fornecedor(**forn_data)
                db.session.add(fornecedor)
                print(f"✓ Fornecedor criado: {forn_data['nome']}")
            else:
                print(f"- Fornecedor já existe: {forn_data['nome']}")
        
        # Salvar mudanças
        try:
            db.session.commit()
            print(f"\n✅ Dados inicializados com sucesso!")
            print(f"📊 Categorias: {Categoria.query.count()}")
            print(f"🏢 Fornecedores: {Fornecedor.query.count()}")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erro ao salvar dados: {e}")

if __name__ == '__main__':
    print("=== Inicializando Dados Padrão ===")
    inicializar_dados_padrao()