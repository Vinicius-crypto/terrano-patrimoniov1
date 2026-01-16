"""
Sistema de Logging Estruturado
Implementação de logging avançado para monitoramento e debugging
"""
import os
import logging
import logging.handlers
from datetime import datetime
import json
from flask import request, g, current_app
try:
    from flask_login import current_user
except ImportError:
    # Fallback se flask_login não estiver disponível
    current_user = None

def get_current_user_info():
    """Helper para obter informações do usuário atual com segurança"""
    if current_user and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
        return {
            'user_id': getattr(current_user, 'id', None),
            'username': getattr(current_user, 'username', None)
        }
    return {'user_id': None, 'username': None}

class StructuredLogger:
    """Logger estruturado para JSON logging"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializar logging na aplicação Flask"""
        
        # Criar diretório de logs
        log_dir = os.path.join(app.instance_path, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Configurar handler para arquivo
        log_file = os.path.join(log_dir, 'app.log')
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        
        # Configurar handler para console
        console_handler = logging.StreamHandler()
        
        # Configurar formatadores
        formatter = StructuredFormatter()
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Configurar níveis
        app.logger.setLevel(logging.INFO)
        file_handler.setLevel(logging.INFO)
        console_handler.setLevel(logging.WARNING)
        
        # Adicionar handlers
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
        
        # Registrar middleware
        app.before_request(self.log_request_info)
        app.after_request(self.log_response_info)
        
        # Configurar logger de segurança separado
        self.setup_security_logger(log_dir)
    
    def setup_security_logger(self, log_dir):
        """Configurar logger específico para eventos de segurança"""
        security_log = os.path.join(log_dir, 'security.log')
        security_handler = logging.handlers.RotatingFileHandler(
            security_log,
            maxBytes=5242880,  # 5MB
            backupCount=20
        )
        
        security_formatter = StructuredFormatter()
        security_handler.setFormatter(security_formatter)
        
        self.security_logger = logging.getLogger('security')
        self.security_logger.setLevel(logging.INFO)
        self.security_logger.addHandler(security_handler)
    
    def log_request_info(self):
        """Log informações da requisição"""
        g.start_time = datetime.utcnow()
        
        log_data = {
            'event': 'request_started',
            'timestamp': g.start_time.isoformat(),
            'method': request.method,
            'url': request.url,
            'endpoint': request.endpoint,
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'user_id': current_user.id if current_user.is_authenticated else None,
            'username': current_user.username if current_user.is_authenticated else None
        }
        
        current_app.logger.info('Request started', extra={'structured': log_data})
    
    def log_response_info(self, response):
        """Log informações da resposta"""
        if hasattr(g, 'start_time'):
            duration = (datetime.utcnow() - g.start_time).total_seconds()
        else:
            duration = None
        
        log_data = {
            'event': 'request_completed',
            'timestamp': datetime.utcnow().isoformat(),
            'status_code': response.status_code,
            'content_length': response.content_length,
            'duration_seconds': duration,
            'method': request.method,
            'url': request.url,
            'endpoint': request.endpoint,
            'user_id': current_user.id if current_user.is_authenticated else None
        }
        
        level = logging.WARNING if response.status_code >= 400 else logging.INFO
        current_app.logger.log(level, f'Request completed with {response.status_code}', 
                              extra={'structured': log_data})
        
        return response
    
    def log_security_event(self, event_type, details):
        """Log evento de segurança"""
        log_data = {
            'event': 'security_event',
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': current_user.id if current_user.is_authenticated else None,
            'username': current_user.username if current_user.is_authenticated else None,
            'remote_addr': request.remote_addr if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None,
            'details': details
        }
        
        self.security_logger.warning(f'Security event: {event_type}', 
                                   extra={'structured': log_data})

class StructuredFormatter(logging.Formatter):
    """Formatador para logs estruturados em JSON"""
    
    def format(self, record):
        # Dados básicos do log
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
        if hasattr(record, 'structured'):
            log_data.update(record.structured)
        
        # Adicionar informações de exceção
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)

# Instância global do logger
structured_logger = StructuredLogger()

def log_user_action(action, details=None):
    """Helper para log de ações do usuário"""
    log_data = {
        'event': 'user_action',
        'action': action,
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': current_user.id if current_user.is_authenticated else None,
        'username': current_user.username if current_user.is_authenticated else None,
        'details': details or {}
    }
    
    current_app.logger.info(f'User action: {action}', extra={'structured': log_data})

def log_equipment_change(equipamento, action, changes=None):
    """Helper para log de mudanças em equipamentos"""
    log_data = {
        'event': 'equipment_change',
        'action': action,
        'equipment_id': equipamento.id_publico,
        'equipment_internal_id': equipamento.id_interno,
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': current_user.id if current_user.is_authenticated else None,
        'changes': changes or {}
    }
    
    current_app.logger.info(f'Equipment {action}: {equipamento.id_publico}', 
                           extra={'structured': log_data})

def log_security_event(event_type, details):
    """Helper para log de eventos de segurança"""
    structured_logger.log_security_event(event_type, details)

def log_performance_metric(metric_name, value, tags=None):
    """Helper para log de métricas de performance"""
    log_data = {
        'event': 'performance_metric',
        'metric': metric_name,
        'value': value,
        'timestamp': datetime.utcnow().isoformat(),
        'tags': tags or {}
    }
    
    current_app.logger.info(f'Performance metric: {metric_name}={value}', 
                           extra={'structured': log_data})