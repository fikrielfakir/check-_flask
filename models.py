from app import db
from flask_login import UserMixin
from datetime import datetime, date
from sqlalchemy import CheckConstraint, Index, text
from sqlalchemy.ext.hybrid import hybrid_property
import json

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100))
    preferences = db.Column(db.Text)  # JSON preferences
    
    # Performance tracking
    cheques_processed = db.Column(db.Integer, default=0)
    average_processing_time = db.Column(db.Float, default=0.0)
    
    # Relationships
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)
    assigned_cheques = db.relationship('Cheque', backref='assigned_user', lazy=True, foreign_keys='Cheque.assigned_user_id')
    
    __table_args__ = (
        CheckConstraint(role.in_(['admin', 'manager', 'employee', 'user']), name='check_user_role'),
        Index('idx_user_role', 'role'),
        Index('idx_user_active', 'is_active'),
    )
    
    def get_preferences(self):
        if self.preferences:
            return json.loads(self.preferences)
        return {}
    
    def set_preferences(self, prefs):
        self.preferences = json.dumps(prefs)

class Bank(db.Model):
    __tablename__ = 'banks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    code = db.Column(db.String(10), unique=True, index=True)
    swift_code = db.Column(db.String(11), index=True)
    icon_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    branches = db.relationship('Branch', backref='bank', lazy=True, cascade='all, delete-orphan')
    
    # Fixed: Access cheques through branches instead of direct relationship
    @property
    def cheques(self):
        """Get all cheques for this bank through its branches"""
        from sqlalchemy.orm import joinedload
        cheques = []
        for branch in self.branches:
            cheques.extend(branch.cheques)
        return cheques
    
    def __repr__(self):
        return f'<Bank {self.name} ({self.code})>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'swift_code': self.swift_code,
            'icon_url': self.icon_url,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Predefined list of Moroccan banks
MOROCCAN_BANKS = [
    {
        "name": "Attijariwafa Bank",
        "code": "AWB",
        "swift_code": "BCMAMAMC",
        "icon_url": "/static/icons/banks/attijariwafa.png"
    },
    {
        "name": "Banque Populaire",
        "code": "BCP",
        "swift_code": "BCPOMAMC",
        "icon_url": "/static/icons/banks/banque_populaire.png"
    },
    {
        "name": "BMCE Bank of Africa",
        "code": "BOA",
        "swift_code": "BMCEAMMC",
        "icon_url": "/static/icons/banks/bmce.png"
    },
    {
        "name": "Crédit Agricole du Maroc",
        "code": "CAM",
        "swift_code": "ACMAMAMC",
        "icon_url": "/static/icons/banks/credit_agricole.png"
    },
    {
        "name": "CIH Bank",
        "code": "CIH",
        "swift_code": "CIHBMAMC",
        "icon_url": "/static/icons/banks/cih.png"
    },
    {
        "name": "Société Générale Maroc",
        "code": "SGMB",
        "swift_code": "SGMBMAMC",
        "icon_url": "/static/icons/banks/societe_generale.png"
    },
    {
        "name": "Al Barid Bank",
        "code": "ABB",
        "swift_code": "BPEIMAMC",
        "icon_url": "/static/icons/banks/albarid.png"
    },
    {
        "name": "Crédit du Maroc",
        "code": "CDM",
        "swift_code": "CDMAMAMC",
        "icon_url": "/static/icons/banks/credit_maroc.png"
    }
]

class Branch(db.Model):
    __tablename__ = 'branches'
    
    id = db.Column(db.Integer, primary_key=True)
    bank_id = db.Column(db.Integer, db.ForeignKey('banks.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    postal_code = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    cheques = db.relationship('Cheque', foreign_keys='Cheque.branch_id', backref='branch', lazy=True)
    
    def __repr__(self):
        return f'<Branch {self.bank.name} - {self.name}>'
    
    @property
    def display_name(self):
        return f"{self.bank.name} - {self.name}"

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    id_number = db.Column(db.String(50))  # CIN or RC
    vat_number = db.Column(db.String(50))  # IF or ICE
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Enhanced client information
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    
    # Risk assessment
    risk_level = db.Column(db.String(20), default='low')  # low, medium, high
    credit_limit = db.Column(db.Numeric(12, 2), default=0)
    current_exposure = db.Column(db.Numeric(12, 2), default=0)
    bounce_rate = db.Column(db.Float, default=0.0)
    
    # AI scoring
    risk_score = db.Column(db.Float, default=0.0)
    last_risk_assessment = db.Column(db.DateTime)
    
    # Communication tracking
    last_contact_date = db.Column(db.DateTime)
    contact_method = db.Column(db.String(50))  # sms, email, phone
    
    # Relationships
    cheques = db.relationship('Cheque', backref='client', lazy=True)
    communications = db.relationship('ClientCommunication', backref='client', lazy=True)
    documents = db.relationship('ClientDocument', backref='client', lazy=True)
    
    __table_args__ = (
        CheckConstraint(type.in_(['personne', 'entreprise']), name='check_client_type'),
        CheckConstraint(risk_level.in_(['low', 'medium', 'high']), name='check_risk_level'),
        Index('idx_client_name', 'name'),
        Index('idx_client_risk', 'risk_level'),
        Index('idx_client_type', 'type'),
    )
    
    @hybrid_property
    def total_cheques_amount(self):
        return sum([c.amount for c in self.cheques])
    
    @hybrid_property
    def pending_cheques_count(self):
        return len([c for c in self.cheques if c.status in ['en_attente', 'depose']])
    
    def calculate_risk_score(self):
        """AI-powered risk scoring algorithm"""
        score = 0
        
        # Bounce rate impact (0-40 points)
        score += min(self.bounce_rate * 40, 40)
        
        # Credit utilization (0-20 points)
        if self.credit_limit > 0:
            utilization = (self.current_exposure / self.credit_limit) * 100
            score += min(utilization * 0.2, 20)
        
        # Historical performance (0-25 points)
        total_cheques = len(self.cheques)
        if total_cheques > 0:
            rejected_cheques = len([c for c in self.cheques if c.status == 'rejete'])
            rejection_rate = (rejected_cheques / total_cheques) * 100
            score += min(rejection_rate * 0.25, 25)
        
        # Time factor (0-15 points)
        if self.last_contact_date:
            days_since_contact = (datetime.utcnow() - self.last_contact_date).days
            score += min(days_since_contact * 0.1, 15)
        
        self.risk_score = min(score, 100)
        self.last_risk_assessment = datetime.utcnow()
        
        # Update risk level based on score
        if self.risk_score < 30:
            self.risk_level = 'low'
        elif self.risk_score < 70:
            self.risk_level = 'medium'
        else:
            self.risk_level = 'high'
        
        return self.risk_score
    
    def __repr__(self):
        return f'<Client {self.name}>'

class Cheque(db.Model):
    __tablename__ = 'cheques'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(10), nullable=False, default='MAD')
    issue_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    deposit_branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)  # Banque de dépôts - Agence
    status = db.Column(db.String(20), nullable=False, default='EN ATTENTE')
    cheque_number = db.Column(db.String(50), unique=True, nullable=False)
    scan_path = db.Column(db.String(255))
    invoice_number = db.Column(db.String(50))
    invoice_date = db.Column(db.Date)
    depositor_name = db.Column(db.String(200))
    notes = db.Column(db.Text)
    payment_type = db.Column(db.String(10), default='CHQ')  # LCN, CHQ, ESP, VIR, VERS
    created_date = db.Column(db.Date)  # User-specified creation date
    unpaid_reason = db.Column(db.Text)  # Reason for unpaid status
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Enhanced tracking
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    processing_time = db.Column(db.Float)  # in hours
    bounce_reason = db.Column(db.String(255))
    
    # Financial intelligence
    commission_rate = db.Column(db.Float, default=0.0)
    commission_amount = db.Column(db.Numeric(10, 2), default=0)
    penalty_amount = db.Column(db.Numeric(10, 2), default=0)
    
    # Status tracking
    deposit_date = db.Column(db.Date)
    clearance_date = db.Column(db.Date)
    rejection_date = db.Column(db.Date)
    
    # OCR and automation
    ocr_confidence = db.Column(db.Float)
    auto_extracted_data = db.Column(db.Text)  # JSON
    duplicate_detected = db.Column(db.Boolean, default=False)
    duplicate_score = db.Column(db.Float, default=0.0)
    
    # Relationships
    status_history = db.relationship('ChequeStatusHistory', backref='cheque', lazy=True)
    deposit_branch = db.relationship('Branch', foreign_keys=[deposit_branch_id], backref='deposit_cheques')
    
    __table_args__ = (
        CheckConstraint(status.in_(['EN ATTENTE', 'ENCAISSE', 'IMPAYE']), 
                       name='check_cheque_status'),
        CheckConstraint(priority.in_(['low', 'normal', 'high', 'urgent']), name='check_priority'),
        CheckConstraint(payment_type.in_(['LCN', 'CHQ', 'ESP', 'VIR', 'VERS']), name='check_payment_type'),
        Index('idx_cheque_status', 'status'),
        Index('idx_cheque_due_date', 'due_date'),
        Index('idx_cheque_client', 'client_id'),
        Index('idx_cheque_branch', 'branch_id'),
        Index('idx_cheque_number', 'cheque_number'),
    )
    
    @hybrid_property
    def age_in_status(self):
        """Calculate days in current status"""
        if self.status_history:
            last_change = max([h.changed_at for h in self.status_history])
            return (datetime.utcnow() - last_change).days
        return (datetime.utcnow() - self.created_at).days
    
    @hybrid_property
    def total_amount_with_fees(self):
        return float(self.amount) + float(self.commission_amount or 0) + float(self.penalty_amount or 0)
    
    def calculate_penalties(self):
        """Calculate penalty for overdue cheques"""
        if self.is_overdue and self.status in ['en_attente', 'depose']:
            days_overdue = (date.today() - self.due_date).days
            daily_penalty_rate = 0.001  # 0.1% per day
            self.penalty_amount = float(self.amount) * daily_penalty_rate * days_overdue
        return self.penalty_amount
    
    def get_ocr_data(self):
        if self.auto_extracted_data:
            return json.loads(self.auto_extracted_data)
        return {}
    
    def set_ocr_data(self, data):
        self.auto_extracted_data = json.dumps(data)
    
    def __repr__(self):
        return f'<Cheque {self.cheque_number}>'
    
    @property
    def status_color(self):
        colors = {
            'en_attente': 'secondary',
            'encaisse': 'success',
            'rejete': 'danger',
            'impaye': 'warning',
            'depose': 'primary',
            'annule': 'light'
        }
        return colors.get(self.status, 'secondary')
    
    @property
    def status_text(self):
        texts = {
            'en_attente': 'EN ATTENTE',
            'encaisse': 'ENCAISSE',
            'rejete': 'REJETE',
        }
        return texts.get(self.status, self.status.upper())
    
    @property
    def is_overdue(self):
        from datetime import date
        return self.due_date < date.today() and self.status in ['en_attente', 'depose']

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    cheque_id = db.Column(db.Integer, db.ForeignKey('cheques.id'))
    
    def __repr__(self):
        return f'<Notification {self.title}>'

# New enhanced models for advanced features
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    table_name = db.Column(db.String(50))
    record_id = db.Column(db.Integer)
    old_values = db.Column(db.Text)  # JSON
    new_values = db.Column(db.Text)  # JSON
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_table', 'table_name'),
        Index('idx_audit_created', 'created_at'),
    )

class ChequeStatusHistory(db.Model):
    __tablename__ = 'cheque_status_history'
    
    id = db.Column(db.Integer, primary_key=True)
    cheque_id = db.Column(db.Integer, db.ForeignKey('cheques.id'), nullable=False)
    old_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    __table_args__ = (
        Index('idx_status_history_cheque', 'cheque_id'),
        Index('idx_status_history_date', 'changed_at'),
    )

# Excel tracking model for optimized synchronization
class ChequeExcelMapping(db.Model):
    __tablename__ = 'cheque_excel_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    cheque_id = db.Column(db.Integer, db.ForeignKey('cheques.id'), nullable=False, unique=True)
    excel_file_path = db.Column(db.String(255), nullable=False)
    sheet_name = db.Column(db.String(50), nullable=False)
    row_number = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cheque = db.relationship('Cheque', backref='excel_mapping', lazy=True)
    
    __table_args__ = (
        Index('idx_excel_mapping_cheque', 'cheque_id'),
        Index('idx_excel_mapping_file', 'excel_file_path'),
        Index('idx_excel_mapping_sheet', 'sheet_name'),
    )
    
    def __repr__(self):
        return f'<ChequeExcelMapping cheque_id={self.cheque_id} sheet={self.sheet_name} row={self.row_number}>'

class ClientCommunication(db.Model):
    __tablename__ = 'client_communications'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # sms, email, phone, letter
    subject = db.Column(db.String(200))
    message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='sent')  # sent, delivered, failed, read
    external_id = db.Column(db.String(100))  # SMS/Email provider ID
    
    __table_args__ = (
        CheckConstraint(type.in_(['sms', 'email', 'phone', 'letter']), name='check_comm_type'),
        CheckConstraint(status.in_(['sent', 'delivered', 'failed', 'read']), name='check_comm_status'),
        Index('idx_comm_client', 'client_id'),
        Index('idx_comm_type', 'type'),
        Index('idx_comm_sent_at', 'sent_at'),
    )

class ClientDocument(db.Model):
    __tablename__ = 'client_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # contract, id, license, etc.
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    __table_args__ = (
        Index('idx_doc_client', 'client_id'),
        Index('idx_doc_type', 'document_type'),
        Index('idx_doc_uploaded_at', 'uploaded_at'),
    )

class DashboardWidget(db.Model):
    __tablename__ = 'dashboard_widgets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    widget_type = db.Column(db.String(50), nullable=False)
    position_x = db.Column(db.Integer, default=0)
    position_y = db.Column(db.Integer, default=0)
    width = db.Column(db.Integer, default=1)
    height = db.Column(db.Integer, default=1)
    configuration = db.Column(db.Text)  # JSON
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_widget_user', 'user_id'),
        Index('idx_widget_active', 'is_active'),
    )

class SystemConfiguration(db.Model):
    __tablename__ = 'system_configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    data_type = db.Column(db.String(20), default='string')  # string, integer, float, boolean, json
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    is_sensitive = db.Column(db.Boolean, default=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_config_key', 'key'),
        Index('idx_config_category', 'category'),
    )

class BackupLog(db.Model):
    __tablename__ = 'backup_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    backup_type = db.Column(db.String(20), nullable=False)  # database, files, full
    status = db.Column(db.String(20), nullable=False)  # success, failed, in_progress
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.BigInteger)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    __table_args__ = (
        CheckConstraint(backup_type.in_(['database', 'files', 'full']), name='check_backup_type'),
        CheckConstraint(status.in_(['success', 'failed', 'in_progress']), name='check_backup_status'),
        Index('idx_backup_started', 'started_at'),
        Index('idx_backup_status', 'status'),
    )

class MoroccanBank(db.Model):
    __tablename__ = 'moroccan_banks'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name_fr = db.Column(db.String(200), nullable=False)
    name_ar = db.Column(db.String(200))
    swift_code = db.Column(db.String(11))
    api_endpoint = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_bank_code', 'code'),
        Index('idx_bank_active', 'is_active'),
    )

class HolidayCalendar(db.Model):
    __tablename__ = 'holiday_calendar'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    name_fr = db.Column(db.String(200), nullable=False)
    name_ar = db.Column(db.String(200))
    type = db.Column(db.String(20), default='national')  # national, religious, bank
    is_banking_day_off = db.Column(db.Boolean, default=True)
    
    __table_args__ = (
        CheckConstraint(type.in_(['national', 'religious', 'bank']), name='check_holiday_type'),
        Index('idx_holiday_date', 'date'),
        Index('idx_holiday_banking', 'is_banking_day_off'),
    )
