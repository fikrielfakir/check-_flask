# Performance optimization utilities
from flask import request, jsonify, g
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import time
import logging

# Cache configuration
cache = Cache()

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def init_performance_tools(app):
    """Initialize performance optimization tools"""
    # Cache configuration
    cache.init_app(app, config={
        'CACHE_TYPE': 'simple',  # Use Redis in production
        'CACHE_DEFAULT_TIMEOUT': 300
    })
    
    # Rate limiter
    limiter.init_app(app)
    
    return cache, limiter

def cache_key_prefix():
    """Generate cache key prefix based on user and request"""
    from flask_login import current_user
    if current_user.is_authenticated:
        return f"user_{current_user.id}"
    return "anonymous"

def cached_query(timeout=300, key_prefix=None):
    """Decorator for caching database queries"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not key_prefix:
                cache_key = f"{cache_key_prefix()}_{func.__name__}_{hash(str(args))}"
            else:
                cache_key = f"{key_prefix}_{func.__name__}"
            
            result = cache.get(cache_key)
            if result is None:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout=timeout)
            return result
        return wrapper
    return decorator

def performance_monitor(func):
    """Monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        
        if duration > 1.0:  # Log slow queries
            logging.warning(f"Slow operation: {func.__name__} took {duration:.2f}s")
        
        return result
    return wrapper

class LazyLoader:
    """Lazy loading for heavy computations"""
    
    @staticmethod
    def load_chart_data(chart_type, filters=None):
        """Load chart data on demand"""
        cache_key = f"chart_{chart_type}_{hash(str(filters))}"
        data = cache.get(cache_key)
        
        if data is None:
            if chart_type == 'monthly_trends':
                data = LazyLoader._get_monthly_trends(filters)
            elif chart_type == 'risk_distribution':
                data = LazyLoader._get_risk_distribution(filters)
            elif chart_type == 'bank_performance':
                data = LazyLoader._get_bank_performance(filters)
            
            cache.set(cache_key, data, timeout=600)
        
        return data
    
    @staticmethod
    def _get_monthly_trends(filters):
        from models import Cheque
        from sqlalchemy import func, extract
        from app import db
        from datetime import datetime, timedelta
        
        query = db.session.query(
            extract('month', Cheque.created_at).label('month'),
            func.count(Cheque.id).label('count'),
            func.sum(Cheque.amount).label('total')
        ).filter(
            Cheque.created_at >= datetime.now() - timedelta(days=365)
        )
        
        if filters:
            if 'status' in filters:
                query = query.filter(Cheque.status == filters['status'])
        
        return [
            {
                'month': row.month,
                'count': row.count,
                'total': float(row.total or 0)
            }
            for row in query.group_by(extract('month', Cheque.created_at)).all()
        ]
    
    @staticmethod
    def _get_risk_distribution(filters):
        from models import Client
        from sqlalchemy import func
        from app import db
        
        return [
            {
                'level': row.risk_level,
                'count': row.count
            }
            for row in db.session.query(
                Client.risk_level,
                func.count(Client.id).label('count')
            ).group_by(Client.risk_level).all()
        ]
    
    @staticmethod
    def _get_bank_performance(filters):
        from models import Bank, Branch, Cheque
        from sqlalchemy import func
        from app import db
        
        return [
            {
                'bank': row.name,
                'processed': row.processed,
                'success_rate': float(row.success_rate or 0)
            }
            for row in db.session.query(
                Bank.name,
                func.count(Cheque.id).label('processed'),
                func.avg(
                    func.case([(Cheque.status == 'ENCAISSE', 1)], else_=0)
                ).label('success_rate')
            ).join(Branch).join(Cheque).group_by(Bank.name).all()
        ]

def compress_response(data):
    """Compress large JSON responses"""
    import gzip
    import json
    
    if isinstance(data, dict) and len(str(data)) > 1000:
        compressed = gzip.compress(json.dumps(data).encode('utf-8'))
        return compressed
    return data

def debounce_search(wait_ms=300):
    """Debounce decorator for search functions"""
    def decorator(func):
        func._last_call = 0
        func._timeout_id = None
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            import threading
            
            current_time = time.time() * 1000
            
            if func._timeout_id:
                func._timeout_id.cancel()
            
            def delayed_call():
                func._last_call = current_time
                return func(*args, **kwargs)
            
            func._timeout_id = threading.Timer(wait_ms / 1000, delayed_call)
            func._timeout_id.start()
            
        return wrapper
    return decorator