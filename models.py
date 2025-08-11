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
    
    # Relationships - Fixed: Remove conflicting backref
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)
    # Remove the backref since we define assigned_user relationship in Cheque model
    assigned_cheques = db.relationship('Cheque', lazy=True, foreign_keys='Cheque.assigned_user_id')
    
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
    
    # Relationships - Fixed: Specify foreign_keys to resolve ambiguity
    # Cheques issued by this branch
    cheques = db.relationship('Cheque', 
                             foreign_keys='Cheque.branch_id',
                             backref='branch', 
                             lazy=True)
    
    # Cheques deposited at this branch
    deposited_cheques = db.relationship('Cheque', 
                                       foreign_keys='Cheque.deposit_branch_id',
                                       backref='deposit_branch', 
                                       lazy=True)
    
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

# Add these new classes to your models.py file

class Depositor(db.Model):
    """Manage people who deposit cheques (depositors)"""
    __tablename__ = 'depositors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    type = db.Column(db.String(20), nullable=False, default='personne')  # personne, entreprise, mandataire
    
    # Contact information
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    
    # Identification
    id_number = db.Column(db.String(50))  # CIN, Passport, RC
    id_type = db.Column(db.String(20))  # cin, passport, rc, ice
    
    # Professional information (for mandataires/employees)
    company_name = db.Column(db.String(200))
    job_title = db.Column(db.String(100))
    authorization_letter_path = db.Column(db.String(255))  # Scan of authorization letter
    
    # Bank account information (optional)
    bank_account_number = db.Column(db.String(50))
    bank_name = db.Column(db.String(100))
    bank_branch = db.Column(db.String(100))
    
    # Activity tracking
    is_active = db.Column(db.Boolean, default=True, index=True)
    registration_date = db.Column(db.Date, default=date.today)
    last_deposit_date = db.Column(db.Date)
    total_deposits = db.Column(db.Integer, default=0)
    total_amount_deposited = db.Column(db.Numeric(15, 2), default=0)
    
    # Risk management
    risk_level = db.Column(db.String(10), default='low')  # low, medium, high
    blocked = db.Column(db.Boolean, default=False)
    blocked_reason = db.Column(db.Text)
    blocked_date = db.Column(db.Date)
    blocked_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Audit fields
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text)
    
    # Relationships
    deposited_cheques = db.relationship('Cheque', backref='depositor', lazy=True)
    deposit_logs = db.relationship('DepositLog', backref='depositor', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (
        CheckConstraint(type.in_(['personne', 'entreprise', 'mandataire']), name='check_depositor_type'),
        CheckConstraint(id_type.in_(['cin', 'passport', 'rc', 'ice', 'carte_sejour']), name='check_id_type'),
        CheckConstraint(risk_level.in_(['low', 'medium', 'high']), name='check_depositor_risk'),
        Index('idx_depositor_name', 'name'),
        Index('idx_depositor_type', 'type'),
        Index('idx_depositor_active', 'is_active'),
        Index('idx_depositor_risk', 'risk_level'),
        Index('idx_depositor_id_number', 'id_number'),
        Index('idx_depositor_registration_date', 'registration_date'),
    )
    
    def __repr__(self):
        return f'<Depositor {self.name}>'
    
    @property
    def display_name(self):
        if self.type == 'mandataire' and self.company_name:
            return f"{self.name} ({self.company_name})"
        return self.name
    
    @property
    def deposit_success_rate(self):
        """Calculate percentage of successful deposits"""
        if self.total_deposits == 0:
            return 100.0
        successful = len([c for c in self.deposited_cheques if c.status in ['ENCAISSE', 'DEPOSE']])
        return (successful / self.total_deposits) * 100
    
    @property
    def recent_activity(self):
        """Check if depositor has been active in the last 30 days"""
        if not self.last_deposit_date:
            return False
        return (date.today() - self.last_deposit_date).days <= 30
    
    def update_stats(self):
        """Update depositor statistics"""
        self.total_deposits = len(self.deposited_cheques)
        self.total_amount_deposited = sum([c.amount for c in self.deposited_cheques])
        if self.deposited_cheques:
            self.last_deposit_date = max([c.created_date for c in self.deposited_cheques])
    
    def calculate_risk_score(self):
        """Calculate risk score based on deposit history"""
        score = 0
        
        if self.total_deposits == 0:
            return 0
        
        # Failed deposits impact
        failed_deposits = len([c for c in self.deposited_cheques if c.status == 'IMPAYE'])
        failure_rate = (failed_deposits / self.total_deposits) * 100
        score += failure_rate * 0.5
        
        # Recent activity
        if not self.recent_activity:
            score += 10
        
        # Amount patterns (large amounts = higher risk)
        if self.total_amount_deposited > 100000:  # More than 100k MAD
            score += 15
        
        return min(score, 100)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'phone': self.phone,
            'email': self.email,
            'id_number': self.id_number,
            'id_type': self.id_type,
            'company_name': self.company_name,
            'is_active': self.is_active,
            'total_deposits': self.total_deposits,
            'total_amount_deposited': float(self.total_amount_deposited) if self.total_amount_deposited else 0,
            'risk_level': self.risk_level,
            'deposit_success_rate': self.deposit_success_rate,
            'recent_activity': self.recent_activity
        }

class DepositLog(db.Model):
    """Log each deposit transaction for audit and tracking"""
    __tablename__ = 'deposit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    depositor_id = db.Column(db.Integer, db.ForeignKey('depositors.id'), nullable=False)
    cheque_id = db.Column(db.Integer, db.ForeignKey('cheques.id'), nullable=False)
    
    # Deposit details
    deposit_date = db.Column(db.Date, nullable=False, default=date.today)
    deposit_time = db.Column(db.Time, default=datetime.now().time)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'))
    teller_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Bank teller who processed
    
    # Verification details
    id_document_verified = db.Column(db.Boolean, default=False)
    authorization_verified = db.Column(db.Boolean, default=False)  # For mandataires
    signature_verified = db.Column(db.Boolean, default=False)
    
    # Transaction details
    deposit_slip_number = db.Column(db.String(50))
    receipt_number = db.Column(db.String(50))
    processing_fee = db.Column(db.Numeric(10, 2), default=0)
    
    # Status and notes
    status = db.Column(db.String(20), default='completed')  # completed, pending_verification, rejected
    rejection_reason = db.Column(db.Text)
    notes = db.Column(db.Text)
    
    # Audit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint(status.in_(['completed', 'pending_verification', 'rejected']), name='check_deposit_status'),
        Index('idx_deposit_log_date', 'deposit_date'),
        Index('idx_deposit_log_depositor', 'depositor_id'),
        Index('idx_deposit_log_cheque', 'cheque_id'),
        Index('idx_deposit_log_branch', 'branch_id'),
        Index('idx_deposit_log_status', 'status'),
    )

class DepositorAuthorization(db.Model):
    """Manage authorizations for mandataires (people authorized to deposit on behalf of others)"""
    __tablename__ = 'depositor_authorizations'
    
    id = db.Column(db.Integer, primary_key=True)
    depositor_id = db.Column(db.Integer, db.ForeignKey('depositors.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    
    # Authorization details
    authorization_type = db.Column(db.String(20), nullable=False)  # permanent, temporary, limited
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)  # NULL for permanent authorizations
    
    # Limits
    max_amount_per_cheque = db.Column(db.Numeric(15, 2))
    max_amount_per_day = db.Column(db.Numeric(15, 2))
    max_amount_per_month = db.Column(db.Numeric(15, 2))
    allowed_branches = db.Column(db.JSON)  # List of branch IDs
    
    # Documentation
    authorization_document_path = db.Column(db.String(255))
    notary_reference = db.Column(db.String(100))
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    revoked_date = db.Column(db.Date)
    revoked_reason = db.Column(db.Text)
    revoked_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Audit
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint(authorization_type.in_(['permanent', 'temporary', 'limited']), name='check_auth_type'),
        Index('idx_auth_depositor', 'depositor_id'),
        Index('idx_auth_client', 'client_id'),
        Index('idx_auth_active', 'is_active'),
        Index('idx_auth_dates', 'start_date', 'end_date'),
    )
    
    def is_valid_for_date(self, check_date=None):
        """Check if authorization is valid for a given date"""
        if check_date is None:
            check_date = date.today()
        
        if not self.is_active:
            return False
            
        if check_date < self.start_date:
            return False
            
        if self.end_date and check_date > self.end_date:
            return False
            
        return True
    
    def is_valid_for_amount(self, amount):
        """Check if authorization allows for a specific amount"""
        if self.max_amount_per_cheque and amount > self.max_amount_per_cheque:
            return False
        return True
    
    def is_valid_for_branch(self, branch_id):
        """Check if authorization allows deposits at a specific branch"""
        if not self.allowed_branches:
            return True  # No restriction
        return branch_id in self.allowed_branches

# Update the Cheque model to use depositor_id instead of depositor_name
# Add this field to the existing Cheque model:

# In your existing Cheque model, add:
# depositor_id = db.Column(db.Integer, db.ForeignKey('depositors.id'), nullable=True)
# 
# And modify the relationship:
# The relationship will be automatically created by the backref in Depositor model

# Migration script to add depositor_id to existing Cheque model
class ChequeDepositorMigration:
    """
    Helper class for migrating existing depositor_name data to new Depositor model
    """
    
    @staticmethod
    def migrate_existing_depositors():
        """
        Migrate existing depositor_name entries to Depositor table
        This should be run as a one-time migration
        """
        from sqlalchemy import text
        
        # Get unique depositor names from existing cheques
        existing_names = db.session.execute(
            text("SELECT DISTINCT depositor_name FROM cheques WHERE depositor_name IS NOT NULL AND depositor_name != ''")
        ).fetchall()
        
        depositor_mapping = {}
        
        for (name,) in existing_names:
            if name and name.strip():
                # Create new depositor
                depositor = Depositor(
                    name=name.strip(),
                    type='personne',  # Default to person
                    created_at=datetime.utcnow()
                )
                db.session.add(depositor)
                db.session.flush()  # To get the ID
                
                depositor_mapping[name] = depositor.id
        
        db.session.commit()
        
        # Update cheques with depositor_id
        for name, depositor_id in depositor_mapping.items():
            db.session.execute(
                text("UPDATE cheques SET depositor_id = :depositor_id WHERE depositor_name = :name"),
                {'depositor_id': depositor_id, 'name': name}
            )
        
        db.session.commit()
        
        return len(depositor_mapping)

# Also add this to your existing models.py for the Cheque model update:
"""
# Add these fields to your existing Cheque model:

# In the Cheque class, add:
depositor_id = db.Column(db.Integer, db.ForeignKey('depositors.id'), nullable=True)

# Keep depositor_name for backward compatibility during migration
# You can remove it later after full migration
# depositor_name = db.Column(db.String(200))  # Keep existing field temporarily

# The depositor relationship will be created automatically via backref in Depositor model
"""

class Cheque(db.Model):
    __tablename__ = 'cheques'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), default='MAD')
    issue_date = db.Column(db.Date)
    due_date = db.Column(db.Date, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    depositor_id = db.Column(db.Integer, db.ForeignKey('depositors.id'), nullable=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    deposit_branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    status = db.Column(db.String(20), default='EN_ATTENTE')
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
    
    # Enhanced Impayé Management Fields
    presentation_date = db.Column(db.Date)  # Date when cheque was presented for collection
    rejection_reason = db.Column(db.String(100))  # Standard rejection reasons
    rejection_notice_path = db.Column(db.String(255))  # Path to rejection notice document
    retry_count = db.Column(db.Integer, default=0)  # Number of retry attempts
    last_retry_date = db.Column(db.Date)  # Date of last retry attempt
    next_retry_date = db.Column(db.Date)  # Scheduled next retry date
    recovery_method = db.Column(db.String(50))  # Alternative payment method used
    recovery_date = db.Column(db.Date)  # Date when recovered via alternative method
    recovery_amount = db.Column(db.Numeric(15, 2))  # Amount recovered
    legal_action_initiated = db.Column(db.Boolean, default=False)  # Legal action flag
    legal_file_reference = db.Column(db.String(100))  # Legal file reference number
    court_case_reference = db.Column(db.String(100))  # Court case reference
    lawyer_name = db.Column(db.String(200))  # Assigned lawyer name
    legal_notes = db.Column(db.Text)  # Legal action notes

    @property
    def days_overdue(self):
        """Calculate days overdue"""
        if self.status in ['ENCAISSE', 'ANNULE']:
            return 0
        if datetime.now().date() <= self.due_date:
            return 0
        return (datetime.now().date() - self.due_date).days
    
    @property
    def is_overdue(self):
        """Check if the cheque is overdue"""
        return self.days_overdue > 0
    
    @property
    def status_display(self):
        status_map = {
            'EN_ATTENTE': 'EN ATTENTE',
            'ENCAISSE': 'ENCAISSÉ',
            'IMPAYE': 'IMPAYÉ',
            'ANNULE': 'ANNULÉ'
        }
        return status_map.get(self.status, self.status)

    @property 
    def status_color(self):
        color_map = {
            'EN_ATTENTE': 'warning',
            'ENCAISSE': 'success',
            'IMPAYE': 'danger',
            'ANNULE': 'secondary'
        }
        return color_map.get(self.status, 'primary')
        
    # Relationships - Fixed: Use back_populates instead of backref to avoid conflicts
    assigned_user = db.relationship('User', back_populates='assigned_cheques')
    excel_mapping = db.relationship('ChequeExcelMapping', backref='cheque', uselist=False, cascade='all, delete-orphan')
    
    # Enhanced Impayé relationships - using string references for forward compatibility
    retry_attempts = db.relationship('ChequeRetryAttempt', backref='cheque', lazy=True, cascade='all, delete-orphan')
    legal_actions = db.relationship('ChequeLegalAction', backref='cheque', lazy=True, cascade='all, delete-orphan')
    impaye_notifications = db.relationship('ImpayeNotification', backref='cheque', lazy=True, cascade='all, delete-orphan')
    
    # Note: branch and deposit_branch relationships are defined in Branch model with foreign_keys specified

# Update User model to use back_populates
User.assigned_cheques = db.relationship('Cheque', back_populates='assigned_user', lazy=True, foreign_keys='Cheque.assigned_user_id')
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

# Enhanced Impayé Management Models

class ChequeRetryAttempt(db.Model):
    """Track retry attempts for bounced cheques"""
    __tablename__ = 'cheque_retry_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    cheque_id = db.Column(db.Integer, db.ForeignKey('cheques.id'), nullable=False)
    attempt_number = db.Column(db.Integer, nullable=False)
    scheduled_date = db.Column(db.Date, nullable=False)
    actual_date = db.Column(db.Date)
    status = db.Column(db.String(20), nullable=False)  # scheduled, completed, failed, cancelled
    result = db.Column(db.String(20))  # success, failed, rejected
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint(status.in_(['scheduled', 'completed', 'failed', 'cancelled']), name='check_retry_status'),
        CheckConstraint(result.in_(['success', 'failed', 'rejected']), name='check_retry_result'),
        Index('idx_retry_cheque', 'cheque_id'),
        Index('idx_retry_scheduled_date', 'scheduled_date'),
        Index('idx_retry_status', 'status'),
    )

class ChequeLegalAction(db.Model):
    """Track legal actions for unpaid cheques"""
    __tablename__ = 'cheque_legal_actions'
    
    id = db.Column(db.Integer, primary_key=True)
    cheque_id = db.Column(db.Integer, db.ForeignKey('cheques.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)  # mise_en_demeure, assignation, jugement, execution
    status = db.Column(db.String(20), nullable=False)  # initiated, in_progress, completed, closed
    file_reference = db.Column(db.String(100))
    court_reference = db.Column(db.String(100))
    lawyer_name = db.Column(db.String(200))
    lawyer_contact = db.Column(db.String(100))
    initiated_date = db.Column(db.Date, nullable=False)
    deadline_date = db.Column(db.Date)
    completion_date = db.Column(db.Date)
    amount_claimed = db.Column(db.Numeric(15, 2))
    amount_recovered = db.Column(db.Numeric(15, 2))
    court_fees = db.Column(db.Numeric(10, 2))
    lawyer_fees = db.Column(db.Numeric(10, 2))
    notes = db.Column(db.Text)
    documents_path = db.Column(db.String(255))  # Path to legal documents
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint(action_type.in_(['mise_en_demeure', 'assignation', 'jugement', 'execution', 'mediation']), name='check_legal_action_type'),
        CheckConstraint(status.in_(['initiated', 'in_progress', 'completed', 'closed', 'suspended']), name='check_legal_status'),
        Index('idx_legal_cheque', 'cheque_id'),
        Index('idx_legal_action_type', 'action_type'),
        Index('idx_legal_status', 'status'),
        Index('idx_legal_initiated_date', 'initiated_date'),
    )

class ImpayeNotification(db.Model):
    """Track notifications sent for bounced cheques"""
    __tablename__ = 'impaye_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    cheque_id = db.Column(db.Integer, db.ForeignKey('cheques.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # impaye_alert, retry_reminder, legal_notice
    recipient_type = db.Column(db.String(20), nullable=False)  # client, internal, lawyer
    recipient_contact = db.Column(db.String(200))
    method = db.Column(db.String(20), nullable=False)  # email, sms, phone, letter
    subject = db.Column(db.String(200))
    message = db.Column(db.Text)
    sent_date = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_status = db.Column(db.String(20), default='sent')  # sent, delivered, failed, read
    delivery_date = db.Column(db.DateTime)
    response_received = db.Column(db.Boolean, default=False)
    response_date = db.Column(db.DateTime)
    response_notes = db.Column(db.Text)
    external_reference = db.Column(db.String(100))  # SMS/Email provider reference
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    __table_args__ = (
        CheckConstraint(notification_type.in_(['impaye_alert', 'retry_reminder', 'legal_notice', 'recovery_notice']), name='check_notification_type'),
        CheckConstraint(recipient_type.in_(['client', 'internal', 'lawyer', 'accountant']), name='check_recipient_type'),
        CheckConstraint(method.in_(['email', 'sms', 'phone', 'letter', 'fax']), name='check_notification_method'),
        CheckConstraint(delivery_status.in_(['sent', 'delivered', 'failed', 'read', 'bounced']), name='check_delivery_status'),
        Index('idx_notification_cheque', 'cheque_id'),
        Index('idx_notification_type', 'notification_type'),
        Index('idx_notification_sent_date', 'sent_date'),
        Index('idx_notification_delivery_status', 'delivery_status'),
    )

class ImpayeRejectionReason(db.Model):
    """Standard rejection reasons for cheques"""
    __tablename__ = 'impaye_rejection_reasons'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    reason_fr = db.Column(db.String(200), nullable=False)
    reason_ar = db.Column(db.String(200))
    category = db.Column(db.String(50))  # funds, signature, account, technical
    severity = db.Column(db.String(10), default='medium')  # low, medium, high
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint(category.in_(['funds', 'signature', 'account', 'technical', 'fraud']), name='check_rejection_category'),
        CheckConstraint(severity.in_(['low', 'medium', 'high']), name='check_rejection_severity'),
        Index('idx_rejection_code', 'code'),
        Index('idx_rejection_category', 'category'),
        Index('idx_rejection_active', 'is_active'),
    )

# Predefined rejection reasons for Moroccan banking system
STANDARD_REJECTION_REASONS = [
    {'code': 'ISF', 'reason_fr': 'Provision insuffisante', 'category': 'funds', 'severity': 'high'},
    {'code': 'SIG', 'reason_fr': 'Signature non conforme', 'category': 'signature', 'severity': 'medium'},
    {'code': 'CMP', 'reason_fr': 'Compte fermé', 'category': 'account', 'severity': 'high'},
    {'code': 'BLQ', 'reason_fr': 'Compte bloqué', 'category': 'account', 'severity': 'high'},
    {'code': 'OPP', 'reason_fr': 'Opposition sur chèque', 'category': 'account', 'severity': 'high'},
    {'code': 'DAT', 'reason_fr': 'Chèque antidaté', 'category': 'technical', 'severity': 'low'},
    {'code': 'EXT', 'reason_fr': 'Chèque expiré', 'category': 'technical', 'severity': 'medium'},
    {'code': 'FRM', 'reason_fr': 'Formulaire non conforme', 'category': 'technical', 'severity': 'low'},
    {'code': 'FRD', 'reason_fr': 'Suspicion de fraude', 'category': 'fraud', 'severity': 'high'},
    {'code': 'AUT', 'reason_fr': 'Autre motif', 'category': 'technical', 'severity': 'medium'}
]