from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DecimalField, DateField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Email, Optional, Length, NumberRange
from wtforms.widgets import TextArea
from models import Bank, Branch, Client
from wtforms import RadioField 

class LoginForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired()])
    password = StringField('Mot de passe', validators=[DataRequired()], render_kw={"type": "password"})
    remember_me = BooleanField('Se souvenir de moi')

class BankForm(FlaskForm):
    name = StringField('Nom de la banque', validators=[DataRequired(), Length(min=2, max=100)])

class BranchForm(FlaskForm):
    name = StringField('Nom de l\'agence', validators=[DataRequired(), Length(min=2, max=100)])
    address = TextAreaField('Adresse', validators=[Optional()])
    postal_code = StringField('Code postal', validators=[Optional(), Length(max=20)])
    phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])

class ClientForm(FlaskForm):
    type = RadioField('Type de client', 
                      choices=[('personne', 'Personne physique'), ('entreprise', 'Entreprise')],
                      validators=[DataRequired()])
    name = StringField('Nom/Raison sociale', validators=[DataRequired(), Length(min=2, max=200)])
    id_number = StringField('CIN/RC', validators=[Optional(), Length(max=50)])
    vat_number = StringField('IF/ICE', validators=[Optional(), Length(max=50)])

class ChequeForm(FlaskForm):
    amount = DecimalField('Montant', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    currency = SelectField('Devise', 
                          choices=[('MAD', 'MAD'), ('EUR', 'EUR'), ('USD', 'USD')],
                          validators=[DataRequired()], default='MAD')
    issue_date = DateField('Date d\'émission', validators=[DataRequired()])
    due_date = DateField('Date d\'échéance', validators=[DataRequired()])
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    branch_id = SelectField('Banque/Agence', coerce=int, validators=[DataRequired()])
    deposit_branch_id = SelectField('Banque de dépôts - Agence', coerce=int, validators=[Optional()])
    status = SelectField('Statut',
                        choices=[
                            ('EN ATTENTE', 'EN ATTENTE'),
                            ('ENCAISSE', 'ENCAISSE'),
                            ('IMPAYE', 'IMPAYE')
                        ],
                        validators=[DataRequired()], default='EN ATTENTE')
    
    payment_type = SelectField('Type de Règlement', 
                             choices=[
                                 ('LCN', 'LCN'),
                                 ('CHQ', 'CHQ'),
                                 ('ESP', 'ESP'),
                                 ('VIR', 'VIR'),
                                 ('VERS', 'VERS')
                             ],
                             validators=[DataRequired()], default='CHQ')
    
    created_date = DateField('Date de Création', validators=[Optional()])
    unpaid_reason = TextAreaField('Raison de l\'impayé', validators=[Optional()])
    cheque_number = StringField('Numéro du chèque', validators=[Optional(), Length(max=50)])
    invoice_number = StringField('N° Facture', validators=[Optional(), Length(max=50)])
    invoice_date = DateField('Date de facture', validators=[Optional()])
    depositor_name = StringField('Nom du déposant', validators=[Optional(), Length(max=200)])
    notes = TextAreaField('Notes', validators=[Optional()])
    scan = FileField('Scan du chèque', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Seuls les fichiers JPG, PNG et PDF sont autorisés.')
    ])
    
    def __init__(self, *args, **kwargs):
        super(ChequeForm, self).__init__(*args, **kwargs)
        
        # Populate client choices
        self.client_id.choices = [(0, 'Sélectionner un client...')] + [
            (client.id, client.name) for client in Client.query.order_by(Client.name).all()
        ]
        
        # Populate branch choices
        branch_choices = [(0, 'Sélectionner une agence...')] + [
            (branch.id, branch.display_name) for branch in Branch.query.join(Bank).order_by(Bank.name, Branch.name).all()
        ]
        self.branch_id.choices = branch_choices
        
        # Populate deposit branch choices (same as branch choices but optional)
        self.deposit_branch_id.choices = [(0, 'Sélectionner une banque de dépôts (optionnel)...')] + [
            (branch.id, branch.display_name) for branch in Branch.query.join(Bank).order_by(Bank.name, Branch.name).all()
        ]
