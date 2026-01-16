# Configuração de Testes

Este arquivo contém a configuração e guias para execução dos testes do sistema.

## Arquivos de Teste

1. **test_suite_simple.py** - Suite principal de testes
   - Testes unitários para utilitários
   - Testes de segurança
   - Testes de lógica de negócio
   - Testes de modelo de dados
   - Testes de integração simulados

## Como Executar os Testes

```bash
# Ativar ambiente virtual
.\venv\Scripts\Activate

# Executar suite completa
python test_suite_simple.py

# Executar testes específicos com unittest
python -m unittest test_suite_simple.UtilsTestCase
python -m unittest test_suite_simple.SecurityTestCase
```

## Cobertura de Testes

A suite atual cobre:
- ✅ Validação de arquivos (extensões permitidas)
- ✅ Formatação de moeda
- ✅ Validação de CNPJ
- ✅ Validação de entrada com regras
- ✅ Rate limiting básico
- ✅ Geração de IDs públicos
- ✅ Cálculo de depreciação
- ✅ Conversão de modelos para dicionário
- ✅ Operações de banco de dados (simuladas)
- ✅ Fluxo completo de cadastro

## Resultados Esperados

- **Taxa de sucesso**: 100%
- **Total de testes**: 10
- **Cobertura**: Excelente

## Próximos Passos

1. Adicionar testes para Flask views (quando app_refatorado.py estiver funcional)
2. Implementar testes de API endpoints
3. Adicionar testes de performance
4. Configurar integração contínua

## Estrutura de Testes

```
tests/
├── test_suite_simple.py      # Suite principal
├── test_config.md            # Este arquivo
└── fixtures/                 # Dados de teste (futuro)
    ├── sample_data.json
    └── test_images/
```

## Dependências de Teste

Os testes atuais são independentes e não requerem dependências externas além de:
- Python unittest (biblioteca padrão)
- sqlite3 (biblioteca padrão)
- datetime (biblioteca padrão)

## Debugging de Testes

Para executar testes com mais verbosidade:

```python
python -m unittest -v test_suite_simple
```

Para executar um teste específico:

```python
python -m unittest test_suite_simple.UtilsTestCase.test_allowed_file_with_valid_extensions
```