from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DecimalField, DateField, BooleanField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Email, Optional, Length, NumberRange
from wtforms.widgets import TextArea, DateInput
from wtforms.fields import Field
from models import Bank, Branch, Client, STANDARD_REJECTION_REASONS
from wtforms import RadioField
from datetime import date, timedelta, datetime

# Custom Date Widget for dd/mm/yyyy format
class CustomDateInput(DateInput):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('type', 'text')  # Use text input instead of HTML5 date
        kwargs.setdefault('data-date-format', 'dd/mm/yyyy')
        kwargs.setdefault('placeholder', 'dd/mm/yyyy')
        kwargs.setdefault('pattern', '\\d{2}/\\d{2}/\\d{4}')
        kwargs.setdefault('title', 'Format: dd/mm/yyyy')
        return super().__call__(field, **kwargs)

# Custom Date Field with dd/mm/yyyy format
class CustomDateField(DateField):
    widget = CustomDateInput()
    
    def _value(self):
        if self.data:
            return self.data.strftime('%d/%m/%Y')
        else:
            return ''
    
    def process_formdata(self, valuelist):
        if valuelist:
            date_str = valuelist[0]
            if date_str:
                try:
                    # Try to parse dd/mm/yyyy format first
                    self.data = datetime.strptime(date_str, '%d/%m/%Y').date()
                except ValueError:
                    try:
                        # Fallback to default format (yyyy-mm-dd)
                        self.data = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        self.data = None
                        raise ValueError('Invalid date format. Use dd/mm/yyyy')
            else:
                self.data = None 

class LoginForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired()])
    password = StringField('Mot de passe', validators=[DataRequired()], render_kw={"type": "password"})
    remember_me = BooleanField('Se souvenir de moi')

class BankForm(FlaskForm):
    name = StringField('Nom de la banque', validators=[DataRequired()])
    code = StringField('Code de la banque', validators=[DataRequired()])
    swift_code = StringField('Code SWIFT', validators=[Optional()])
    icon_url = StringField('URL de l\'icône', validators=[Optional()])
    is_active = BooleanField('Banque active', default=True)

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
    phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    address = TextAreaField('Adresse', validators=[Optional()])
    city = StringField('Ville', validators=[Optional(), Length(max=100)])
    postal_code = StringField('Code postal', validators=[Optional(), Length(max=20)])

class DepositorForm(FlaskForm):
    name = StringField('Nom complet', validators=[DataRequired(), Length(min=2, max=200)])
    type = SelectField('Type de déposant', 
                      choices=[
                          ('personne', 'Personne physique'),
                          ('entreprise', 'Entreprise'),
                          ('mandataire', 'Mandataire/Agent')
                      ], validators=[DataRequired()])
    
    # Contact information
    phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    address = TextAreaField('Adresse', validators=[Optional()])
    city = StringField('Ville', validators=[Optional(), Length(max=100)])
    postal_code = StringField('Code postal', validators=[Optional(), Length(max=20)])
    
    # Identification
    id_number = StringField('Numéro d\'identification', validators=[Optional(), Length(max=50)])
    id_type = SelectField('Type d\'identifiant', 
                         choices=[
                             ('cin', 'CIN'),
                             ('passport', 'Passeport'),
                             ('carte_sejour', 'Carte de séjour'),
                             ('rc', 'Registre de commerce'),
                             ('ice', 'ICE')
                         ], validators=[Optional()])
    
    # Company information (for entreprise and mandataire types)
    company_name = StringField('Nom de l\'entreprise', validators=[Optional(), Length(max=200)])
    job_title = StringField('Poste occupé', validators=[Optional(), Length(max=100)])
    
    # Bank information (optional)
    bank_account_number = StringField('Numéro de compte', validators=[Optional(), Length(max=50)])
    bank_name = StringField('Nom de la banque', validators=[Optional(), Length(max=100)])
    bank_branch = StringField('Agence bancaire', validators=[Optional(), Length(max=100)])
    
    # Notes
    notes = TextAreaField('Notes', validators=[Optional()])
    is_active = BooleanField('Déposant actif', default=True)

class ChequeForm(FlaskForm):
    amount = DecimalField('Mont', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    currency = SelectField('Devise', 
                          choices=[('MAD', 'MAD'), ('EUR', 'EUR'), ('USD', 'USD')],
                          validators=[DataRequired()], default='MAD')
    issue_date = CustomDateField('Date réc', validators=[DataRequired()])
    due_date = CustomDateField('Date d\'échéance', validators=[DataRequired()])
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    depositor_id = SelectField('Déposant', coerce=int, validators=[Optional()])
    branch_id = SelectField('Bq/Agce', coerce=int, validators=[DataRequired()])
    deposit_branch_id = SelectField('Bq dép. - Agce', coerce=int, validators=[Optional()])
    status = SelectField('Statut',
                        choices=[
                            ('EN_ATTENTE', 'EN ATTENTE'),
                            ('PRESENTE', 'PRÉSENTE'),
                            ('EN_COURS', 'EN COURS'),
                            ('ENCAISSE', 'ENCAISSÉ'),
                            ('IMPAYE', 'IMPAYÉ'),
                            ('TENTATIVE', 'NOUVELLE TENTATIVE'),
                            ('RECOUVRE', 'RECOUVRÉ'),
                            ('PROCEDURE', 'PROCÉDURE LÉGALE'),
                            ('DEPOSE', 'DÉPOSÉ'),
                            ('ANNULE', 'ANNULÉ')
                        ],
                        validators=[DataRequired()], default='EN_ATTENTE')
    
    payment_type = SelectField('Type rég', 
                             choices=[
                                 ('LCN', 'LCN'),
                                 ('CHQ', 'CHQ'),
                                 ('ESP', 'ESP'),
                                 ('VIR', 'VIR'),
                                 ('VERS', 'VERS')
                             ],
                             validators=[DataRequired()], default='CHQ')
    
    created_date = CustomDateField('Date créat', validators=[Optional()])
    unpaid_reason = TextAreaField('Raison de l\'impayé', validators=[Optional()])
    
    # Enhanced Impayé Management Fields
    presentation_date = CustomDateField('Date de présentation', validators=[Optional()])
    rejection_reason = SelectField('Motif de rejet', choices=[], validators=[Optional()])
    rejection_notice = FileField('Avis de rejet', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Seuls les fichiers JPG, PNG et PDF sont autorisés.')
    ])
    recovery_method = SelectField('Méthode de recouvrement', 
                                 choices=[
                                     ('', 'Sélectionner...'),
                                     ('cash', 'Espèces'),
                                     ('transfer', 'Virement bancaire'),
                                     ('check', 'Nouveau chèque'),
                                     ('installments', 'Paiement échelonné'),
                                     ('other', 'Autre')
                                 ], validators=[Optional()])
    recovery_date = CustomDateField('Date de recouvrement', validators=[Optional()])
    recovery_amount = DecimalField('Mont recouvré', validators=[Optional(), NumberRange(min=0)], places=2)
    next_retry_date = CustomDateField('Prochaine tentative prévue', validators=[Optional()])
    legal_action_initiated = BooleanField('Action légale initiée')
    legal_file_reference = StringField('Référence du dossier légal', validators=[Optional(), Length(max=100)])
    court_case_reference = StringField('Référence du tribunal', validators=[Optional(), Length(max=100)])
    lawyer_name = StringField('Nom de l\'avocat', validators=[Optional(), Length(max=200)])
    legal_notes = TextAreaField('Notes légales', validators=[Optional()])
    cheque_number = StringField('N° doc', validators=[Optional(), Length(max=50)])
    invoice_number = StringField('N° Facture', validators=[Optional(), Length(max=50)])
    invoice_date = CustomDateField('Date fact', validators=[Optional()])
    depositor_name = StringField('Nom dép', validators=[Optional(), Length(max=200)])
    notes = TextAreaField('Notes', validators=[Optional()])
    scan = FileField('Scan du chèque', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Seuls les fichiers JPG, PNG et PDF sont autorisés.')
    ])
    
    def __init__(self, *args, **kwargs):
        super(ChequeForm, self).__init__(*args, **kwargs)
        
        # Import here to avoid circular imports
        from models import Depositor
        
        # Populate client choices - Safe approach
        try:
            # Try to filter by is_active first
            clients = Client.query.filter_by(is_active=True).order_by(Client.name).all()
        except Exception:
            # If is_active doesn't exist, get all clients
            clients = Client.query.order_by(Client.name).all()
        
        self.client_id.choices = [(0, 'Sélectionner un client...')] + [
            (c.id, f"{c.name} ({'Entreprise' if c.type == 'entreprise' else 'Personne'})")
            for c in clients
        ]
    
        
        # Populate depositor choices
        self.depositor_id.choices = [(0, 'Sélectionner un déposant...')] + [
            (d.id, f"{d.name} ({'Entreprise' if d.type == 'entreprise' else 'Personne' if d.type == 'personne' else 'Mandataire'})")
            for d in Depositor.query.filter_by(is_active=True, blocked=False).order_by(Depositor.name).all()
        ]
        
        # Populate branch choices (Bank - Branch format)
        branches = Branch.query.join(Bank).filter(
            Branch.active == True,
            Bank.is_active == True
        ).order_by(Bank.name, Branch.name).all()
        self.branch_id.choices = [(0, 'Sélectionner une agence...')] + [
            (branch.id, f"{branch.bank.name} - {branch.name}") 
            for branch in branches
        ]
        
        # Populate deposit branch choices (same as branch choices)
        self.deposit_branch_id.choices = [(0, 'Sélectionner une agence de dépôt...')] + [
            (branch.id, f"{branch.bank.name} - {branch.name}") 
            for branch in branches
        ]
        
        # Populate rejection reason choices
        self.rejection_reason.choices = [('', 'Sélectionner un motif...')] + [
            (reason['code'], reason['reason_fr']) for reason in STANDARD_REJECTION_REASONS
        ]

# Enhanced Impayé Management Forms

class ImpayeStatusForm(FlaskForm):
    """Form for marking a cheque as Impayé (bounced)"""
    cheque_id = HiddenField()
    rejection_date = CustomDateField('Date de rejet', validators=[DataRequired()], default=date.today)
    rejection_reason = SelectField('Motif de rejet', validators=[DataRequired()])
    rejection_notice = FileField('Avis de rejet (optionnel)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Seuls les fichiers JPG, PNG et PDF sont autorisés.')
    ])
    notes = TextAreaField('Notes complémentaires', validators=[Optional()])
    notify_client = BooleanField('Notifier le client', default=True)
    notification_method = SelectField('Méthode de notification', 
                                    choices=[
                                        ('email', 'Email'),
                                        ('sms', 'SMS'),
                                        ('phone', 'Téléphone'),
                                        ('letter', 'Courrier')
                                    ], validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(ImpayeStatusForm, self).__init__(*args, **kwargs)
        self.rejection_reason.choices = [(reason['code'], reason['reason_fr']) for reason in STANDARD_REJECTION_REASONS]

class RetryAttemptForm(FlaskForm):
    """Form for scheduling retry attempts"""
    cheque_id = HiddenField()
    scheduled_date = CustomDateField('Date prévue pour la tentative', validators=[DataRequired()])
    notes = TextAreaField('Notes pour cette tentative', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(RetryAttemptForm, self).__init__(*args, **kwargs)
        # Default to 7 days from today
        if not self.scheduled_date.data:
            self.scheduled_date.data = date.today() + timedelta(days=7)

class RetryResultForm(FlaskForm):
    """Form for recording retry attempt results"""
    retry_id = HiddenField()
    actual_date = CustomDateField('Date réelle de la tentative', validators=[DataRequired()], default=date.today)
    result = SelectField('Résultat', 
                        choices=[
                            ('success', 'Succès - Chèque encaissé'),
                            ('failed', 'Échec - Nouveau rejet'),
                            ('rejected', 'Rejeté - Même motif')
                        ], validators=[DataRequired()])
    new_rejection_reason = SelectField('Nouveau motif de rejet (si applicable)', choices=[])
    notes = TextAreaField('Notes sur cette tentative', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(RetryResultForm, self).__init__(*args, **kwargs)
        self.new_rejection_reason.choices = [('', 'Aucun/Non applicable')] + [
            (reason['code'], reason['reason_fr']) for reason in STANDARD_REJECTION_REASONS
        ]

class AlternativePaymentForm(FlaskForm):
    """Form for recording alternative payment received"""
    cheque_id = HiddenField()
    recovery_method = SelectField('Méthode de recouvrement', 
                                 choices=[
                                     ('cash', 'Espèces'),
                                     ('transfer', 'Virement bancaire'),
                                     ('check', 'Nouveau chèque'),
                                     ('installments', 'Paiement échelonné'),
                                     ('discount', 'Remise accordée'),
                                     ('other', 'Autre')
                                 ], validators=[DataRequired()])
    recovery_date = CustomDateField('Date de recouvrement', validators=[DataRequired()], default=date.today)
    recovery_amount = DecimalField('Mont recouvré', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    recovery_reference = StringField('Référence du paiement', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('Notes sur le recouvrement', validators=[Optional()])

class LegalActionForm(FlaskForm):
    """Form for initiating legal action"""
    cheque_id = HiddenField()
    action_type = SelectField('Type d\'action légale', 
                             choices=[
                                 ('mise_en_demeure', 'Mise en demeure'),
                                 ('assignation', 'Assignation en justice'),
                                 ('mediation', 'Médiation'),
                                 ('execution', 'Exécution forcée')
                             ], validators=[DataRequired()])
    initiated_date = CustomDateField('Date d\'initiation', validators=[DataRequired()], default=date.today)
    deadline_date = CustomDateField('Date limite/échéance', validators=[Optional()])
    file_reference = StringField('Référence du dossier', validators=[Optional(), Length(max=100)])
    court_reference = StringField('Référence tribunal', validators=[Optional(), Length(max=100)])
    lawyer_name = StringField('Nom de l\'avocat', validators=[Optional(), Length(max=200)])
    lawyer_contact = StringField('Contact avocat', validators=[Optional(), Length(max=100)])
    amount_claimed = DecimalField('Mont réclamé', validators=[DataRequired(), NumberRange(min=0.01)], places=2)
    court_fees = DecimalField('Frais de justice', validators=[Optional(), NumberRange(min=0)], places=2)
    lawyer_fees = DecimalField('Honoraires avocat', validators=[Optional(), NumberRange(min=0)], places=2)
    legal_documents = FileField('Documents légaux', validators=[
        FileAllowed(['pdf', 'doc', 'docx'], 'Seuls les fichiers PDF et DOC sont autorisés.')
    ])
    notes = TextAreaField('Notes légales', validators=[Optional()])


class DepositorForm(FlaskForm):
    """Form for managing depositor information"""
    name = StringField('Nom complet', validators=[DataRequired(), Length(min=2, max=200)])
    type = SelectField('Type de déposant', 
                      choices=[
                          ('personne', 'Personne physique'),
                          ('entreprise', 'Entreprise'),
                          ('mandataire', 'Mandataire')
                      ],
                      validators=[DataRequired()])
    
    # Contact information
    phone = StringField('Téléphone', validators=[Optional(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    address = TextAreaField('Adresse', validators=[Optional()])
    city = StringField('Ville', validators=[Optional(), Length(max=100)])
    postal_code = StringField('Code postal', validators=[Optional(), Length(max=20)])
    
    # Identification
    id_number = StringField('Numéro d\'identification', validators=[Optional(), Length(max=50)])
    id_type = SelectField('Type de pièce d\'identité',
                         choices=[
                             ('', 'Sélectionner...'),
                             ('cin', 'CIN'),
                             ('passport', 'Passeport'),
                             ('rc', 'Registre de Commerce'),
                             ('ice', 'ICE'),
                             ('carte_sejour', 'Carte de séjour')
                         ],
                         validators=[Optional()])
    
    # Professional information (for mandataires/employees)
    company_name = StringField('Nom de l\'entreprise', validators=[Optional(), Length(max=200)])
    job_title = StringField('Poste/Fonction', validators=[Optional(), Length(max=100)])
    
    # Bank account information (optional)
    bank_account_number = StringField('Numéro de compte bancaire', validators=[Optional(), Length(max=50)])
    bank_name = StringField('Nom de la banque', validators=[Optional(), Length(max=100)])
    bank_branch = StringField('Agence bancaire', validators=[Optional(), Length(max=100)])
    
    # Notes
    notes = TextAreaField('Notes et observations', validators=[Optional()])

class NotificationForm(FlaskForm):
    """Form for sending notifications about impayé cheques"""
    cheque_id = HiddenField()
    notification_type = SelectField('Type de notification', 
                                   choices=[
                                       ('impaye_alert', 'Alerte impayé'),
                                       ('retry_reminder', 'Rappel tentative'),
                                       ('legal_notice', 'Avis légal'),
                                       ('recovery_notice', 'Avis de recouvrement')
                                   ], validators=[DataRequired()])
    recipient_type = SelectField('Destinataire', 
                                choices=[
                                    ('client', 'Client'),
                                    ('internal', 'Interne'),
                                    ('lawyer', 'Avocat'),
                                    ('accountant', 'Comptable')
                                ], validators=[DataRequired()])
    method = SelectField('Méthode', 
                        choices=[
                            ('email', 'Email'),
                            ('sms', 'SMS'),
                            ('phone', 'Téléphone'),
                            ('letter', 'Courrier')
                        ], validators=[DataRequired()])
    recipient_contact = StringField('Contact du destinataire', validators=[DataRequired(), Length(max=200)])
    subject = StringField('Sujet', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Message', validators=[DataRequired()], render_kw={'rows': 6})
    
class PresentationForm(FlaskForm):
    """Form for marking cheque as presented for collection"""
    cheque_id = HiddenField()
    presentation_date = CustomDateField('Date de présentation', validators=[DataRequired()], default=date.today)
    notes = TextAreaField('Notes', validators=[Optional()])
    notify_stakeholders = BooleanField('Notifier les parties prenantes', default=True)
