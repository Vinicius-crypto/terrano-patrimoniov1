#!/usr/bin/env python3
"""
Script para limpar dados duplicados de código de barras
"""

from app import app, db, Equipamento

def limpar_codigos_barras_duplicados():
    """Remove códigos de barras vazios duplicados"""
    
    with app.app_context():
        # Buscar equipamentos com código de barras vazio
        equipamentos_vazios = Equipamento.query.filter(
            (Equipamento.codigo_barras == '') | 
            (Equipamento.codigo_barras.is_(None))
        ).all()
        
        print(f"Encontrados {len(equipamentos_vazios)} equipamentos com código de barras vazio/nulo")
        
        # Converter strings vazias para NULL
        count_updated = 0
        for equipamento in equipamentos_vazios:
            if equipamento.codigo_barras == '':
                equipamento.codigo_barras = None
                count_updated += 1
                print(f"✓ Equipamento {equipamento.id_publico}: código de barras limpo")
        
        # Salvar mudanças
        try:
            db.session.commit()
            print(f"\n✅ {count_updated} registros atualizados com sucesso!")
            print("Agora você pode cadastrar novos equipamentos normalmente.")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erro ao atualizar registros: {e}")

if __name__ == '__main__':
    print("=== Limpeza de Códigos de Barras Duplicados ===")
    limpar_codigos_barras_duplicados()