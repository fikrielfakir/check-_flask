"""
Utility decorators for the cheque management application
"""

from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def role_required(allowed_roles):
    """
    Decorator to restrict access based on user roles.
    
    Args:
        allowed_roles (list): List of allowed roles ['admin', 'comptable', 'agent', 'user']
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Vous devez être connecté pour accéder à cette page.', 'error')
                return redirect(url_for('auth.login'))
            
            if current_user.role not in allowed_roles:
                flash('Vous n\'avez pas les permissions nécessaires pour accéder à cette page.', 'error')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator to restrict access to admin users only."""
    return role_required(['admin'])(f)


def comptable_required(f):
    """Decorator to restrict access to admin and comptable users."""
    return role_required(['admin', 'comptable'])(f)


def agent_required(f):
    """Decorator to restrict access to admin, comptable, and agent users."""
    return role_required(['admin', 'comptable', 'agent'])(f)