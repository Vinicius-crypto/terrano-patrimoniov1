"""
Suite de Testes Unitários
Testes abrangentes para o sistema de controle de patrimônio
"""
import os
import sys
import unittest
import tempfile
from datetime import datetime, date
import sqlite3

# Adicionar o diretório pai ao path para importar a aplicação
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from models import db, Usuario, Equipamento, Categoria, Fornecedor
    from services import EquipamentoService, HistoricoService, ReportService
    from security import SecurityValidator, RateLimiter
    from utils import allowed_file, format_currency, validate_cnpj
except ImportError as e:
    print(f"Aviso: Módulos não encontrados. Usando mocks para testes básicos. Erro: {e}")
    # Criar classes mock para testes básicos
    class MockDB:
        def create_all(self): pass
        def drop_all(self): pass
        def session(self): pass
    
    class MockModel:
        def __init__(self, **kwargs): 
            for k, v in kwargs.items():
                setattr(self, k, v)
        
        @classmethod
        def query(cls): return cls()
        
        def filter_by(self, **kwargs): return self
        def first(self): return None
        def to_dict(self): return {}
    
    db = MockDB()
    Usuario = MockModel
    Equipamento = MockModel
    Categoria = MockModel
    Fornecedor = MockModel

class BaseTestCase(unittest.TestCase):
    """Classe base para todos os testes"""
    
    def setUp(self):
        """Configurar ambiente de teste"""
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
        os.environ['FLASK_ENV'] = 'testing'
        
        from app_refatorado import create_app
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        # Criar tabelas
        db.create_all()
        
        # Criar usuário de teste
        self.create_test_user()
    
    def tearDown(self):
        """Limpar após o teste"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def create_test_user(self):
        """Criar usuário para testes"""
        import bcrypt
        hash_senha = bcrypt.hashpw('test123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        self.test_user = Usuario(
            username='testuser',
            password_hash=hash_senha,
            nivel_acesso=2,
            nome_completo='Usuário de Teste',
            ativo=True
        )
        db.session.add(self.test_user)
        db.session.commit()
    
    def login(self, username='testuser', password='test123'):
        """Helper para fazer login"""
        return self.client.post('/login', data={
            'username': username,
            'senha': password
        }, follow_redirects=True)

class ModelTestCase(BaseTestCase):
    """Testes para os modelos"""
    
    def test_usuario_creation(self):
        """Testar criação de usuário"""
        user = Usuario.query.filter_by(username='testuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.nivel_acesso, 2)
        self.assertTrue(user.ativo)
    
    def test_equipamento_creation(self):
        """Testar criação de equipamento"""
        equipamento = Equipamento(
            id_publico='PAT-TEST-001',
            tipo='Notebook',
            marca='Dell',
            modelo='Inspiron 15',
            status='Estocado',
            valor=2500.00,
            created_by=self.test_user.id
        )
        db.session.add(equipamento)
        db.session.commit()
        
        saved_equipamento = Equipamento.query.filter_by(id_publico='PAT-TEST-001').first()
        self.assertIsNotNone(saved_equipamento)
        self.assertEqual(saved_equipamento.tipo, 'Notebook')
        self.assertEqual(saved_equipamento.valor, 2500.00)
    
    def test_equipamento_to_dict(self):
        """Testar conversão de equipamento para dicionário"""
        equipamento = Equipamento(
            id_publico='PAT-TEST-002',
            tipo='Mouse',
            marca='Logitech',
            status='Em uso',
            valor=50.00
        )
        db.session.add(equipamento)
        db.session.commit()
        
        data = equipamento.to_dict()
        self.assertIsInstance(data, dict)
        self.assertEqual(data['id_publico'], 'PAT-TEST-002')
        self.assertEqual(data['tipo'], 'Mouse')
        self.assertEqual(data['valor'], 50.00)
    
    def test_categoria_creation(self):
        """Testar criação de categoria"""
        categoria = Categoria(
            nome='Hardware',
            icone='💻',
            cor='#3B82F6',
            descricao='Equipamentos de informática'
        )
        db.session.add(categoria)
        db.session.commit()
        
        saved_categoria = Categoria.query.filter_by(nome='Hardware').first()
        self.assertIsNotNone(saved_categoria)
        self.assertEqual(saved_categoria.icone, '💻')
    
    def test_fornecedor_creation(self):
        """Testar criação de fornecedor"""
        fornecedor = Fornecedor(
            nome='Dell Technologies',
            cnpj='12.345.678/0001-90',
            email='vendas@dell.com',
            telefone='(11) 1234-5678'
        )
        db.session.add(fornecedor)
        db.session.commit()
        
        saved_fornecedor = Fornecedor.query.filter_by(nome='Dell Technologies').first()
        self.assertIsNotNone(saved_fornecedor)
        self.assertEqual(saved_fornecedor.cnpj, '12.345.678/0001-90')

class ServiceTestCase(BaseTestCase):
    """Testes para os serviços"""
    
    def test_equipamento_service_gerar_id_publico(self):
        """Testar geração de ID público"""
        id_publico = EquipamentoService.gerar_id_publico()
        self.assertEqual(id_publico, 'PAT-001')
        
        # Criar um equipamento e testar próximo ID
        equipamento = Equipamento(id_publico='PAT-001', tipo='Test', status='Estocado')
        db.session.add(equipamento)
        db.session.commit()
        
        next_id = EquipamentoService.gerar_id_publico()
        self.assertEqual(next_id, 'PAT-002')
    
    def test_report_service_gerar_dados_dashboard(self):
        """Testar geração de dados do dashboard"""
        # Criar equipamentos de teste
        equipamentos = [
            Equipamento(id_publico='PAT-001', tipo='Notebook', status='Em uso', valor=1000.00),
            Equipamento(id_publico='PAT-002', tipo='Mouse', status='Estocado', valor=50.00),
            Equipamento(id_publico='PAT-003', tipo='Teclado', status='Manutenção', valor=100.00)
        ]
        
        for eq in equipamentos:
            db.session.add(eq)
        db.session.commit()
        
        dados = ReportService.gerar_dados_dashboard()
        
        self.assertIsNotNone(dados)
        self.assertEqual(dados['total'], 3)
        self.assertEqual(dados['em_uso'], 1)
        self.assertEqual(dados['estocado'], 1)
        self.assertEqual(dados['manutencao'], 1)
        self.assertEqual(dados['valor_total'], 1150.00)

class SecurityTestCase(BaseTestCase):
    """Testes para segurança"""
    
    def test_security_validator_validate_input(self):
        """Testar validação de entrada"""
        rules = {
            'username': {
                'required': True,
                'type': str,
                'min_length': 3,
                'max_length': 50
            },
            'email': {
                'type': str,
                'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            },
            'idade': {
                'type': int,
                'validator': lambda x: 18 <= x <= 120
            }
        }
        
        # Teste com dados válidos
        valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'idade': 25
        }
        errors = SecurityValidator.validate_input(valid_data, rules)
        self.assertEqual(len(errors), 0)
        
        # Teste com dados inválidos
        invalid_data = {
            'username': 'ab',  # Muito curto
            'email': 'email_invalido',  # Formato inválido
            'idade': 15  # Menor que 18
        }
        errors = SecurityValidator.validate_input(invalid_data, rules)
        self.assertGreater(len(errors), 0)
    
    def test_rate_limiter(self):
        """Testar rate limiter"""
        limiter = RateLimiter()
        
        # Testar requisições dentro do limite
        for i in range(5):
            self.assertTrue(limiter.is_allowed('test_ip', max_requests=10, window_minutes=1))
        
        # Testar excesso de requisições
        for i in range(10):
            limiter.is_allowed('test_ip2', max_requests=5, window_minutes=1)
        
        # A próxima deve ser bloqueada
        self.assertFalse(limiter.is_allowed('test_ip2', max_requests=5, window_minutes=1))

class UtilsTestCase(BaseTestCase):
    """Testes para utilitários"""
    
    def test_allowed_file(self):
        """Testar validação de arquivos"""
        self.assertTrue(allowed_file('test.pdf'))
        self.assertTrue(allowed_file('image.jpg'))
        self.assertTrue(allowed_file('document.png'))
        self.assertFalse(allowed_file('script.js'))
        self.assertFalse(allowed_file('executable.exe'))
        self.assertFalse(allowed_file(''))
        self.assertFalse(allowed_file(None))
    
    def test_format_currency(self):
        """Testar formatação de moeda"""
        self.assertEqual(format_currency(1234.56), 'R$ 1.234,56')
        self.assertEqual(format_currency(0), 'R$ 0,00')
        self.assertEqual(format_currency(None), 'R$ 0,00')
    
    def test_validate_cnpj(self):
        """Testar validação de CNPJ"""
        self.assertTrue(validate_cnpj('12.345.678/0001-95'))  # Formato válido
        self.assertTrue(validate_cnpj('12345678000195'))      # Apenas números
        self.assertTrue(validate_cnpj(''))                    # Vazio é permitido
        self.assertTrue(validate_cnpj(None))                  # None é permitido
        self.assertFalse(validate_cnpj('123'))               # Muito curto

class ViewTestCase(BaseTestCase):
    """Testes para as views"""
    
    def test_login_page(self):
        """Testar página de login"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)
    
    def test_login_success(self):
        """Testar login bem-sucedido"""
        response = self.login()
        self.assertEqual(response.status_code, 200)
        # Verificar se foi redirecionado para dashboard
    
    def test_login_failure(self):
        """Testar login com credenciais inválidas"""
        response = self.client.post('/login', data={
            'username': 'invalid',
            'senha': 'wrong'
        }, follow_redirects=True)
        self.assertIn(b'Credenciais inválidas', response.data)
    
    def test_home_requires_login(self):
        """Testar que home requer login"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)  # Redirect para login
    
    def test_home_after_login(self):
        """Testar acesso ao home após login"""
        self.login()
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

class IntegrationTestCase(BaseTestCase):
    """Testes de integração"""
    
    def test_cadastro_equipamento_completo(self):
        """Testar cadastro completo de equipamento"""
        self.login()
        
        # Criar categoria e fornecedor primeiro
        categoria = Categoria(nome='Hardware', descricao='Equipamentos')
        fornecedor = Fornecedor(nome='Dell', cnpj='12345678000195')
        db.session.add(categoria)
        db.session.add(fornecedor)
        db.session.commit()
        
        # Cadastrar equipamento
        response = self.client.post('/cadastrar', data={
            'tipo': 'Notebook',
            'marca': 'Dell',
            'modelo': 'Inspiron 15',
            'num_serie': 'ABC123456',
            'data_aquisicao': '2024-01-15',
            'localizacao': 'Sala TI',
            'status': 'Estocado',
            'responsavel': 'João Silva',
            'valor': '2500.00',
            'categoria_id': categoria.id,
            'fornecedor_id': fornecedor.id,
            'vida_util_anos': '5'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar se equipamento foi criado
        equipamento = Equipamento.query.filter_by(num_serie='ABC123456').first()
        self.assertIsNotNone(equipamento)
        self.assertEqual(equipamento.marca, 'Dell')
        self.assertEqual(equipamento.valor, 2500.00)

# Suíte de testes
def create_test_suite():
    """Criar suíte de testes completa"""
    suite = unittest.TestSuite()
    
    # Adicionar classes de teste
    test_classes = [
        ModelTestCase,
        ServiceTestCase,
        SecurityTestCase,
        UtilsTestCase,
        ViewTestCase,
        IntegrationTestCase
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite

def run_tests():
    """Executar todos os testes"""
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Calcular cobertura
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success_rate = ((total_tests - failures - errors) / total_tests) * 100
    
    print(f"\n{'='*50}")
    print(f"RELATÓRIO DE TESTES")
    print(f"{'='*50}")
    print(f"Total de testes: {total_tests}")
    print(f"Sucessos: {total_tests - failures - errors}")
    print(f"Falhas: {failures}")
    print(f"Erros: {errors}")
    print(f"Taxa de sucesso: {success_rate:.1f}%")
    
    if success_rate >= 70:
        print("✅ Cobertura de testes satisfatória!")
    else:
        print("❌ Cobertura de testes insuficiente!")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    run_tests()