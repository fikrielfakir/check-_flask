from app import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import text

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Bank(db.Model):
    __tablename__ = 'banks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    website = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    branches = db.relationship('Branch', backref='bank', lazy=True, cascade='all, delete-orphan')

class Branch(db.Model):
    __tablename__ = 'branches'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20))
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    manager_name = db.Column(db.String(100))
    bank_id = db.Column(db.Integer, db.ForeignKey('banks.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cheques = db.relationship('Cheque', foreign_keys='Cheque.branch_id', backref='branch', lazy=True)
    deposit_cheques = db.relationship('Cheque', foreign_keys='Cheque.deposit_branch_id', backref='deposit_branch', lazy=True)

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20), default='person')  # person or company
    cin = db.Column(db.String(20))  # For person
    rc = db.Column(db.String(50))   # For company
    ice = db.Column(db.String(50))  # For company
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cheques = db.relationship('Cheque', backref='client', lazy=True)

class Cheque(db.Model):
    __tablename__ = 'cheques'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), default='MAD')
    issue_date = db.Column(db.Date)
    due_date = db.Column(db.Date, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    deposit_branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    status = db.Column(db.String(20), default='EN ATTENTE')
    cheque_number = db.Column(db.String(50))
    scan_path = db.Column(db.String(255))
    invoice_number = db.Column(db.String(100))
    invoice_date = db.Column(db.Date)
    depositor_name = db.Column(db.String(200))
    notes = db.Column(db.Text)
    payment_type = db.Column(db.String(20), default='CHQ')
    created_date = db.Column(db.Date, default=datetime.utcnow().date)
    unpaid_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional fields for enhanced functionality
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    priority = db.Column(db.String(10), default='NORMALE')
    processing_time = db.Column(db.Integer)
    bounce_reason = db.Column(db.Text)
    commission_rate = db.Column(db.Numeric(5, 2))
    commission_amount = db.Column(db.Numeric(10, 2))
    penalty_amount = db.Column(db.Numeric(10, 2))
    deposit_date = db.Column(db.Date)
    clearance_date = db.Column(db.Date)
    rejection_date = db.Column(db.Date)
    ocr_confidence = db.Column(db.Numeric(5, 2))
    auto_extracted_data = db.Column(db.JSON)
    duplicate_detected = db.Column(db.Boolean, default=False)
    duplicate_score = db.Column(db.Numeric(5, 2))
    
    # Relationships
    assigned_user = db.relationship('User', backref='assigned_cheques')
    excel_mapping = db.relationship('ChequeExcelMapping', backref='cheque', uselist=False, cascade='all, delete-orphan')

class ChequeExcelMapping(db.Model):
    """Track Excel sheet and row mappings for each cheque"""
    __tablename__ = 'cheque_excel_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    cheque_id = db.Column(db.Integer, db.ForeignKey('cheques.id'), nullable=False, unique=True)
    excel_file_path = db.Column(db.String(500), nullable=False)
    sheet_name = db.Column(db.String(100), nullable=False)
    row_number = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    cheque_id = db.Column(db.Integer, db.ForeignKey('cheques.id'))
    type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    cheque = db.relationship('Cheque', backref='notifications')

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    table_name = db.Column(db.String(50))
    record_id = db.Column(db.Integer)
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='audit_logs')

class SystemSettings(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AnalyticsCache(db.Model):
    __tablename__ = 'analytics_cache'
    
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.JSON)
    date_computed = db.Column(db.Date, nullable=False)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('metric_name', 'date_computed'),)

# Create indexes for better performance
def create_indexes():
    """Create database indexes for better query performance"""
    try:
        with db.engine.connect() as conn:
            # Cheques indexes
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_cheques_due_date ON cheques(due_date)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_cheques_status ON cheques(status)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_cheques_client_id ON cheques(client_id)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_cheques_branch_id ON cheques(branch_id)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_cheques_deposit_branch_id ON cheques(deposit_branch_id)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_cheques_cheque_number ON cheques(cheque_number)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_cheques_created_at ON cheques(created_at)'))
            
            # Excel mappings indexes
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_excel_mappings_cheque_id ON cheque_excel_mappings(cheque_id)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_excel_mappings_file_sheet ON cheque_excel_mappings(excel_file_path, sheet_name)'))
            
            # Clients indexes
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(name)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_clients_cin ON clients(cin)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_clients_rc ON clients(rc)'))
            
            # Branches indexes
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_branches_bank_id ON branches(bank_id)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_branches_name ON branches(name)'))
            
            # Notifications indexes
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read)'))
            
            conn.commit()
            print("Database indexes created successfully")
    except Exception as e:
        print(f"Error creating indexes: {str(e)}")