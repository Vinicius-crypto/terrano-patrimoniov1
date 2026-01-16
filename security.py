"""
Middleware de Segurança Avançado
Rate Limiting, Validações e Headers de Segurança
"""
import time
import hashlib
from functools import wraps
from collections import defaultdict, deque
from datetime import datetime, timedelta
from flask import request, jsonify, abort, current_app, g
from flask_login import current_user

class RateLimiter:
    """Rate limiter baseado em IP e usuário"""
    
    def __init__(self):
        self.requests = defaultdict(deque)
        self.blocked_ips = {}
    
    def is_allowed(self, identifier, max_requests=60, window_minutes=1):
        """Verificar se a requisição está dentro do limite"""
        now = datetime.now()
        window = timedelta(minutes=window_minutes)
        
        # Limpar requisições antigas
        cutoff = now - window
        while self.requests[identifier] and self.requests[identifier][0] < cutoff:
            self.requests[identifier].popleft()
        
        # Verificar se está bloqueado
        if identifier in self.blocked_ips:
            if now < self.blocked_ips[identifier]:
                return False
            else:
                del self.blocked_ips[identifier]
        
        # Verificar limite
        if len(self.requests[identifier]) >= max_requests:
            # Bloquear por 15 minutos
            self.blocked_ips[identifier] = now + timedelta(minutes=15)
            current_app.logger.warning(f"Rate limit exceeded for {identifier}")
            return False
        
        # Registrar requisição
        self.requests[identifier].append(now)
        return True

class SecurityValidator:
    """Validador de entrada e segurança"""
    
    @staticmethod
    def validate_input(data, rules):
        """Validar dados de entrada com regras específicas"""
        errors = []
        
        for field, rule in rules.items():
            value = data.get(field)
            
            # Verificar se campo é obrigatório
            if rule.get('required', False) and not value:
                errors.append(f"Campo '{field}' é obrigatório")
                continue
            
            if value is None:
                continue
            
            # Verificar tipo
            expected_type = rule.get('type')
            if expected_type and not isinstance(value, expected_type):
                if expected_type == str and isinstance(value, (int, float)):
                    value = str(value)
                else:
                    errors.append(f"Campo '{field}' deve ser do tipo {expected_type.__name__}")
                    continue
            
            # Verificar tamanho mínimo e máximo
            if isinstance(value, str):
                min_len = rule.get('min_length')
                max_len = rule.get('max_length')
                
                if min_len and len(value) < min_len:
                    errors.append(f"Campo '{field}' deve ter pelo menos {min_len} caracteres")
                
                if max_len and len(value) > max_len:
                    errors.append(f"Campo '{field}' deve ter no máximo {max_len} caracteres")
            
            # Verificar padrões regex
            pattern = rule.get('pattern')
            if pattern and isinstance(value, str):
                import re
                if not re.match(pattern, value):
                    errors.append(f"Campo '{field}' não está no formato correto")
            
            # Validações customizadas
            validator = rule.get('validator')
            if validator and callable(validator):
                try:
                    if not validator(value):
                        errors.append(f"Campo '{field}' não passou na validação")
                except Exception as e:
                    errors.append(f"Erro na validação do campo '{field}': {str(e)}")
        
        return errors
    
    @staticmethod
    def sanitize_string(text, max_length=1000):
        """Sanitizar string removendo caracteres perigosos"""
        if not isinstance(text, str):
            return text
        
        # Remover caracteres de controle
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Limitar tamanho
        if len(text) > max_length:
            text = text[:max_length]
        
        return text.strip()
    
    @staticmethod
    def validate_file_upload(file, allowed_extensions, max_size_mb=5):
        """Validar arquivo de upload"""
        errors = []
        
        if not file or not file.filename:
            return ['Nenhum arquivo foi enviado']
        
        # Verificar extensão
        if '.' not in file.filename:
            errors.append('Arquivo deve ter uma extensão')
        else:
            ext = file.filename.rsplit('.', 1)[1].lower()
            if ext not in allowed_extensions:
                errors.append(f'Extensão não permitida. Permitidas: {", ".join(allowed_extensions)}')
        
        # Verificar tamanho (Flask já limita, mas validamos novamente)
        file.seek(0, 2)  # Ir para o final
        size = file.tell()
        file.seek(0)  # Voltar ao início
        
        if size > max_size_mb * 1024 * 1024:
            errors.append(f'Arquivo muito grande. Máximo: {max_size_mb}MB')
        
        return errors

class SecurityHeaders:
    """Middleware para adicionar headers de segurança"""
    
    @staticmethod
    def add_security_headers(response):
        """Adicionar headers de segurança à resposta"""
        # Proteção XSS
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # CSP básico
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self';"
        )
        response.headers['Content-Security-Policy'] = csp
        
        # HSTS (apenas em HTTPS)
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response

# Instâncias globais
rate_limiter = RateLimiter()
security_validator = SecurityValidator()

def rate_limit(max_requests=60, window_minutes=1):
    """Decorator para rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Identificador baseado em IP + usuário (se logado)
            identifier = request.remote_addr
            if current_user.is_authenticated:
                identifier = f"{identifier}:{current_user.id}"
            
            if not rate_limiter.is_allowed(identifier, max_requests, window_minutes):
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': 'Muitas requisições. Tente novamente em alguns minutos.'
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_json(rules):
    """Decorator para validação de JSON"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type deve ser application/json'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'JSON inválido ou vazio'}), 400
            
            errors = security_validator.validate_input(data, rules)
            if errors:
                return jsonify({'error': 'Dados inválidos', 'details': errors}), 400
            
            g.validated_data = data
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def login_required_api(f):
    """Decorator para endpoints API que exigem login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Login necessário'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator para endpoints que exigem permissão de admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Login necessário'}), 401
        
        if current_user.nivel_acesso < 3:
            return jsonify({'error': 'Permissão insuficiente'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def log_security_event(event_type):
    """Decorator para log automático de eventos de segurança"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                
                # Log do evento
                from logging_config import log_security_event
                log_security_event(event_type, {
                    'function': f.__name__,
                    'success': True,
                    'args': str(args) if args else None,
                    'kwargs': str(kwargs) if kwargs else None
                })
                
                return result
            except Exception as e:
                # Log do erro de segurança
                from logging_config import log_security_event
                log_security_event(f"{event_type}_failed", {
                    'function': f.__name__,
                    'success': False,
                    'error': str(e),
                    'args': str(args) if args else None,
                    'kwargs': str(kwargs) if kwargs else None
                })
                raise
        return decorated_function
    return decorator

def init_security_middleware(app):
    """Inicializar middleware de segurança na aplicação"""
    
    @app.before_request
    def security_checks():
        """Verificações de segurança antes de cada requisição"""
        
        # Rate limiting para login
        if request.endpoint == 'login' and request.method == 'POST':
            identifier = f"login:{request.remote_addr}"
            if not rate_limiter.is_allowed(identifier, max_requests=5, window_minutes=15):
                from logging_config import log_security_event
                log_security_event('login_rate_limit_exceeded', {
                    'ip': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent')
                })
                abort(429)
        
        # Verificar User-Agent suspeito
        user_agent = request.headers.get('User-Agent', '')
        suspicious_agents = ['sqlmap', 'nmap', 'nikto', 'burp', 'acunetix']
        if any(agent in user_agent.lower() for agent in suspicious_agents):
            from logging_config import log_security_event
            log_security_event('suspicious_user_agent', {
                'ip': request.remote_addr,
                'user_agent': user_agent,
                'endpoint': request.endpoint
            })
            abort(403)
    
    @app.after_request
    def add_security_headers(response):
        """Adicionar headers de segurança"""
        return SecurityHeaders.add_security_headers(response)
    
    # Registrar handlers de erro de segurança
    @app.errorhandler(429)
    def rate_limit_handler(e):
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Muitas requisições. Tente novamente mais tarde.'
        }), 429
    
    @app.errorhandler(403)
    def forbidden_handler(e):
        return jsonify({
            'error': 'Forbidden',
            'message': 'Acesso negado.'
        }), 403