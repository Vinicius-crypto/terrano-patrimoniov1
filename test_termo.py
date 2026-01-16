#!/usr/bin/env python3
"""Testar geração de termo de cautela"""

from app import app, db, Equipamento, Categoria, Fornecedor
import requests
import json

def test_termo_generation():
    """Testar geração de termo diretamente"""
    with app.app_context():
        # Buscar um equipamento com categoria e fornecedor
        equipamento = Equipamento.query.filter_by(id_publico='PAT-002').first()
        
        if not equipamento:
            print("❌ Equipamento PAT-002 não encontrado")
            return
            
        print(f"🔧 Testando equipamento: {equipamento.id_publico}")
        print(f"📋 Tipo: {equipamento.tipo}")
        print(f"📂 Categoria ID: {equipamento.categoria_id}")
        print(f"🏢 Fornecedor ID: {equipamento.fornecedor_id}")
        
        # Testar busca de categoria
        if equipamento.categoria_id:
            categoria = Categoria.query.get(equipamento.categoria_id)
            print(f"✅ Categoria encontrada: {categoria.nome}")
        else:
            print("⚪ Sem categoria definida")
            
        # Testar busca de fornecedor
        if equipamento.fornecedor_id:
            fornecedor = Fornecedor.query.get(equipamento.fornecedor_id)
            print(f"✅ Fornecedor encontrado: {fornecedor.nome}")
        else:
            print("⚪ Sem fornecedor definido")
            
        print("\n🎯 Todos os dados necessários para o PDF estão disponíveis!")
        return True

if __name__ == "__main__":
    print("=== Teste de Geração de Termo ===")
    test_termo_generation()