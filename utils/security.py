# Security enhancements
import pyotp
import qrcode
from io import BytesIO
import base64
from cryptography.fernet import Fernet
from flask import request, session, current_app
from flask_login import current_user
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from functools import wraps
import logging

class TwoFactorAuth:
    """Two-Factor Authentication implementation"""
    
    @staticmethod
    def generate_secret():
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(user, secret):
        """Generate QR code for 2FA setup"""
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            user.email,
            issuer_name="Cheque Management System"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    @staticmethod
    def verify_token(secret, token):
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    @staticmethod
    def require_2fa(func):
        """Decorator to require 2FA for sensitive operations"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return {'error': 'Authentication required'}, 401
            
            if hasattr(current_user, 'two_factor_enabled') and current_user.two_factor_enabled:
                if not session.get('2fa_verified'):
                    return {'error': '2FA verification required'}, 403
            
            return func(*args, **kwargs)
        return wrapper

class DataEncryption:
    """Data encryption utilities"""
    
    def __init__(self, key=None):
        if key:
            self.key = key
        else:
            self.key = current_app.config.get('ENCRYPTION_KEY') or Fernet.generate_key()
        self.cipher_suite = Fernet(self.key)
    
    def encrypt_sensitive_data(self, data):
        """Encrypt sensitive data"""
        if not data:
            return None
        return self.cipher_suite.encrypt(str(data).encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data):
        """Decrypt sensitive data"""
        if not encrypted_data:
            return None
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()

class AuditLogger:
    """Comprehensive audit logging"""
    
    @staticmethod
    def log_action(action, table_name=None, record_id=None, old_values=None, new_values=None):
        """Log user action for audit trail"""
        from models import AuditLog
        from app import db
        
        try:
            audit_entry = AuditLog(
                user_id=current_user.id if current_user.is_authenticated else None,
                action=action,
                table_name=table_name,
                record_id=record_id,
                old_values=old_values,
                new_values=new_values,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', ''),
                timestamp=datetime.utcnow()
            )
            
            db.session.add(audit_entry)
            db.session.commit()
            
        except Exception as e:
            logging.error(f"Failed to log audit entry: {e}")
    
    @staticmethod
    def audit_action(action, table_name=None):
        """Decorator for automatic audit logging"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Capture data before modification
                old_values = None
                if table_name and len(args) > 0:
                    try:
                        old_values = args[0].__dict__.copy() if hasattr(args[0], '__dict__') else None
                    except:
                        pass
                
                result = func(*args, **kwargs)
                
                # Capture data after modification
                new_values = None
                if table_name and len(args) > 0:
                    try:
                        new_values = args[0].__dict__.copy() if hasattr(args[0], '__dict__') else None
                    except:
                        pass
                
                # Log the action
                record_id = None
                if hasattr(result, 'id'):
                    record_id = result.id
                elif len(args) > 0 and hasattr(args[0], 'id'):
                    record_id = args[0].id
                
                AuditLogger.log_action(action, table_name, record_id, old_values, new_values)
                
                return result
            return wrapper
        return decorator

class SecurityHeaders:
    """Security headers middleware"""
    
    @staticmethod
    def add_security_headers(response):
        """Add security headers to response"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "font-src 'self' cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
        return response

class SessionSecurity:
    """Enhanced session security"""
    
    @staticmethod
    def secure_session_config(app):
        """Configure secure session settings"""
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
    
    @staticmethod
    def validate_session_integrity():
        """Validate session integrity"""
        if 'user_id' in session:
            # Check for session hijacking
            expected_signature = SessionSecurity._generate_session_signature()
            actual_signature = session.get('session_signature')
            
            if not hmac.compare_digest(str(expected_signature), str(actual_signature or '')):
                session.clear()
                return False
        return True
    
    @staticmethod
    def _generate_session_signature():
        """Generate session signature for integrity check"""
        user_agent = request.headers.get('User-Agent', '')
        ip_address = request.remote_addr
        user_id = session.get('user_id', '')
        
        signature_data = f"{user_agent}{ip_address}{user_id}"
        return hashlib.sha256(signature_data.encode()).hexdigest()
    
    @staticmethod
    def setup_session_signature():
        """Setup session signature after login"""
        session['session_signature'] = SessionSecurity._generate_session_signature()
        session['login_time'] = datetime.utcnow().isoformat()

class RateLimitingAdvanced:
    """Advanced rate limiting with dynamic thresholds"""
    
    @staticmethod
    def adaptive_rate_limit(base_limit=10, window=60):
        """Adaptive rate limiting based on user behavior"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                user_key = f"rate_limit_{current_user.id if current_user.is_authenticated else request.remote_addr}"
                
                # Get user's success rate
                success_rate = RateLimitingAdvanced._get_user_success_rate()
                
                # Adjust limit based on success rate
                adjusted_limit = int(base_limit * (1 + success_rate))
                
                # Check rate limit
                if RateLimitingAdvanced._check_rate_limit(user_key, adjusted_limit, window):
                    return func(*args, **kwargs)
                else:
                    return {'error': 'Rate limit exceeded'}, 429
            return wrapper
        return decorator
    
    @staticmethod
    def _get_user_success_rate():
        """Calculate user's success rate for adaptive limiting"""
        # Implementation would check recent successful vs failed requests
        return 0.8  # Placeholder
    
    @staticmethod
    def _check_rate_limit(key, limit, window):
        """Check if request is within rate limit"""
        # Implementation would use Redis or in-memory store
        return True  # Placeholder

def require_permissions(permissions):
    """Decorator to require specific permissions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return {'error': 'Authentication required'}, 401
            
            user_permissions = current_user.role_permissions
            
            for permission in permissions:
                if permission not in user_permissions:
                    AuditLogger.log_action(f"UNAUTHORIZED_ACCESS_ATTEMPT: {permission}")
                    return {'error': 'Insufficient permissions'}, 403
            
            return func(*args, **kwargs)
        return wrapper
    return decorator