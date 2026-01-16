#!/usr/bin/env python3
"""
Script para testar relacionamentos e geração de termos
"""

from app import app, db, Equipamento, Categoria, Fornecedor

def testar_relacionamentos():
    """Testa se os relacionamentos estão funcionando"""
    
    with app.app_context():
        # Buscar equipamentos
        equipamentos = Equipamento.query.all()
        print(f"📋 Total de equipamentos: {len(equipamentos)}")
        
        for equipamento in equipamentos:
            print(f"\n🔧 {equipamento.id_publico} - {equipamento.tipo}")
            print(f"   📂 Categoria ID: {equipamento.categoria_id}")
            print(f"   🏢 Fornecedor ID: {equipamento.fornecedor_id}")
            
            # Testar categoria
            if equipamento.categoria_id:
                categoria = Categoria.query.get(equipamento.categoria_id)
                print(f"   ✅ Categoria: {categoria.nome if categoria else 'ERROR'}")
            else:
                print(f"   ⚪ Categoria: Não definida")
            
            # Testar fornecedor
            if equipamento.fornecedor_id:
                fornecedor = Fornecedor.query.get(equipamento.fornecedor_id)  
                print(f"   ✅ Fornecedor: {fornecedor.nome if fornecedor else 'ERROR'}")
            else:
                print(f"   ⚪ Fornecedor: Não definido")

if __name__ == '__main__':
    print("=== Teste de Relacionamentos ===")
    testar_relacionamentos()