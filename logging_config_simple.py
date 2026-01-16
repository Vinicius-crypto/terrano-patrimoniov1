"""
Sistema de Logging Simplificado
Implementação básica de logging para o sistema
"""
import os
import logging
import logging.handlers
from datetime import datetime
import json

def get_current_user_info():
    """Helper para obter informações do usuário atual com segurança"""
    try:
        from flask_login import current_user
        if current_user and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            return {
                'user_id': getattr(current_user, 'id', None),
                'username': getattr(current_user, 'username', None)
            }
    except ImportError:
        pass
    return {'user_id': None, 'username': None}

class SimpleStructuredLogger:
    """Logger estruturado simplificado"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializar com aplicação Flask"""
        self.app = app
        
        # Configurar diretório de logs
        log_dir = app.config.get('LOG_DIR', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Configurar nível de log
        log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper())
        
        # Configurar handler de arquivo
        log_file = os.path.join(log_dir, 'app.log')
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        
        # Configurar formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        # Adicionar handler ao logger da aplicação
        app.logger.addHandler(file_handler)
        app.logger.setLevel(log_level)
        
        # Log de inicialização
        app.logger.info('Sistema de logging inicializado')
    
    def log_request(self, request):
        """Log de requisição HTTP"""
        try:
            from flask import request as flask_request, g
            user_info = get_current_user_info()
            
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'method': flask_request.method,
                'url': flask_request.url,
                'ip': flask_request.remote_addr,
                'user_agent': str(flask_request.user_agent),
                'user_id': user_info['user_id'],
                'username': user_info['username']
            }
            
            if self.app:
                self.app.logger.info(f'Request: {flask_request.method} {flask_request.path}', 
                                   extra={'structured': log_data})
        except Exception as e:
            if self.app:
                self.app.logger.error(f'Erro no log de requisição: {e}')
    
    def log_response(self, response):
        """Log de resposta HTTP"""
        try:
            from flask import request as flask_request
            user_info = get_current_user_info()
            
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'status_code': response.status_code,
                'response_size': len(response.get_data()),
                'user_id': user_info['user_id']
            }
            
            level = logging.INFO if response.status_code < 400 else logging.WARNING
            
            if self.app:
                self.app.logger.log(level, 
                                  f'Response: {response.status_code} for {flask_request.method} {flask_request.path}',
                                  extra={'structured': log_data})
        except Exception as e:
            if self.app:
                self.app.logger.error(f'Erro no log de resposta: {e}')
    
    def log_error(self, error, context=None):
        """Log de erro com contexto"""
        try:
            user_info = get_current_user_info()
            
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': context or {},
                'user_id': user_info['user_id'],
                'username': user_info['username']
            }
            
            if self.app:
                self.app.logger.error(f'Erro: {type(error).__name__}: {str(error)}',
                                    extra={'structured': log_data})
        except Exception as e:
            if self.app:
                self.app.logger.error(f'Erro no log de erro: {e}')

class SimpleJSONFormatter(logging.Formatter):
    """Formatter simples para JSON"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Adicionar dados estruturados se disponíveis
        if hasattr(record, 'structured') and hasattr(record.structured, 'items'):
            try:
                log_data.update(record.structured)
            except (TypeError, AttributeError):
                pass
        
        return json.dumps(log_data, ensure_ascii=False, default=str)

# Funções de conveniência
def log_user_action(action, details=None):
    """Log de ação do usuário"""
    try:
        from flask import current_app
        user_info = get_current_user_info()
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details or {},
            'user_id': user_info['user_id'],
            'username': user_info['username']
        }
        
        current_app.logger.info(f'Ação do usuário: {action}', extra={'structured': log_data})
    except Exception:
        pass

def log_equipment_action(action, equipamento, details=None):
    """Log de ação em equipamento"""
    try:
        from flask import current_app
        user_info = get_current_user_info()
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'equipment_id': getattr(equipamento, 'id_publico', None),
            'equipment_type': getattr(equipamento, 'tipo', None),
            'details': details or {},
            'user_id': user_info['user_id']
        }
        
        current_app.logger.info(f'Equipamento {action}: {getattr(equipamento, "id_publico", "N/A")}',
                              extra={'structured': log_data})
    except Exception:
        pass

def log_performance_metric(metric_name, value, context=None):
    """Log de métrica de performance"""
    try:
        from flask import current_app
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'metric_name': metric_name,
            'value': value,
            'context': context or {}
        }
        
        current_app.logger.info(f'Métrica de performance: {metric_name}={value}',
                              extra={'structured': log_data})
    except Exception:
        pass

# Instância global
structured_logger = SimpleStructuredLogger()