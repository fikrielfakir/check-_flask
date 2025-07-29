import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    
    # Configuration for Replit environment
    app.secret_key = os.environ.get("SESSION_SECRET", "KSr8293NEv711HU16ZIr14Hxp13hv_ghVJVJgAgxkwo")
    
    # Use PostgreSQL database for Replit environment with SQLite fallback for development
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        # Fallback to SQLite for local development
        db_path = os.path.join(os.getcwd(), "data", "cheques.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["WTF_CSRF_ENABLED"] = True
    # Configure folders for uploads and exports
    app.config["UPLOAD_FOLDER"] = os.path.join(os.getcwd(), "uploads")
    app.config["EXCEL_FOLDER"] = os.path.join(os.getcwd(), "data", "excel")
    app.config["EXPORTS_FOLDER"] = os.path.join(os.getcwd(), "data", "exports")
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size
    
    # Ensure all directories exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["EXCEL_FOLDER"], exist_ok=True)
    os.makedirs(app.config["EXPORTS_FOLDER"], exist_ok=True)
    
    # Initialize extensions
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.banks import banks_bp
    from routes.clients import clients_bp
    from routes.cheques import cheques_bp
    from routes.exports import exports_bp
    from routes.excel_manager import excel_manager_bp
    from routes.analytics import analytics_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(banks_bp, url_prefix='/banks')
    app.register_blueprint(clients_bp, url_prefix='/clients')
    app.register_blueprint(cheques_bp, url_prefix='/cheques')
    app.register_blueprint(exports_bp, url_prefix='/exports')
    app.register_blueprint(excel_manager_bp, url_prefix='/excel')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    
    with app.app_context():
        # Import models to ensure they're registered
        import models
        
        # Create all database tables
        db.create_all()
        
        # Create default admin user if not exists
        from models import User
        from werkzeug.security import generate_password_hash
        
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            logging.info("Default admin user created (username: admin, password: admin123)")
        else:
            logging.info("Admin user already exists")
    
    return app

# Create the app instance
app = create_app()

# Initialize scheduler for notifications
from scheduler import init_scheduler
init_scheduler(app)
