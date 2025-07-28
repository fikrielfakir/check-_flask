from app import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import CheckConstraint

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    __table_args__ = (
        CheckConstraint(role.in_(['admin', 'comptable', 'agent', 'user']), name='check_user_role'),
    )

class Bank(db.Model):
    __tablename__ = 'banks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    branches = db.relationship('Branch', backref='bank', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Bank {self.name}>'

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
    
    # Relationship
    cheques = db.relationship('Cheque', backref='branch', lazy=True)
    
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
    
    # Relationship
    cheques = db.relationship('Cheque', backref='client', lazy=True)
    
    __table_args__ = (
        CheckConstraint(type.in_(['personne', 'entreprise']), name='check_client_type'),
    )
    
    def __repr__(self):
        return f'<Client {self.name}>'

class Cheque(db.Model):
    __tablename__ = 'cheques'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), nullable=False, default='MAD')
    issue_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='en_attente')
    cheque_number = db.Column(db.String(50))
    scan_path = db.Column(db.String(255))
    invoice_number = db.Column(db.String(50))
    invoice_date = db.Column(db.Date)
    depositor_name = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint(status.in_(['en_attente', 'encaisse', 'rejete', 'impaye', 'depose', 'annule']), 
                       name='check_cheque_status'),
    )
    
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
            'encaisse': 'ENCAISSÉ',
            'rejete': 'REJETÉ',
            'impaye': 'IMPAYÉ',
            'depose': 'DÉPOSÉ',
            'annule': 'ANNULÉ'
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
