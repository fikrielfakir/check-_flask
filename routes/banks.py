from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Bank, Branch, db
from forms import BankForm, BranchForm
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import uuid

banks_bp = Blueprint('banks', __name__)

# Liste des banques marocaines (13 banques)
MOROCCAN_BANKS = [
    {
        "name": "Attijariwafa Bank",
        "code": "AWB",
        "swift_code": "BCMAMAMC",
        "icon": "attijariwafa.png",
        "type": "commercial"
    },
    {
        "name": "Banque Populaire du Maroc",
        "code": "BCP",
        "swift_code": "BCPOMAMC",
        "icon": "banque_populaire.png",
        "type": "commercial"
    },
    {
        "name": "BMCE Bank of Africa",
        "code": "BMCE",
        "swift_code": "BMCEAMMC",
        "icon": "bmce.png",
        "type": "commercial"
    },
    {
        "name": "Crédit Agricole du Maroc",
        "code": "CAM",
        "swift_code": "ACMAMAMC",
        "icon": "credit_agricole.png",
        "type": "commercial"
    },
    {
        "name": "CIH Bank",
        "code": "CIH",
        "swift_code": "CIHBMAMC",
        "icon": "cih.png",
        "type": "commercial"
    },
    {
        "name": "Société Générale Maroc",
        "code": "SGMB",
        "swift_code": "SGMBMAMC",
        "icon": "societe_generale.png",
        "type": "commercial"
    },
    {
        "name": "Al Barid Bank",
        "code": "ABB",
        "swift_code": "BPEIMAMC",
        "icon": "albarid.png",
        "type": "commercial"
    },
    {
        "name": "BMCI - Bank of Africa",
        "code": "BMCI",
        "swift_code": "BMCIMAMC",
        "icon": "bmci.png",
        "type": "commercial"
    },
    {
        "name": "CDM - Crédit du Maroc",
        "code": "CDM",
        "swift_code": "CDMAMAMC",
        "icon": "cdm.png",
        "type": "commercial"
    },
    {
        "name": "Umnia Bank",
        "code": "UMB",
        "swift_code": "UMNIAMC",
        "icon": "umnia.png",
        "type": "participatif"
    },
    {
        "name": "Al Yousr Bank",
        "code": "AYB",
        "swift_code": "ALYOUMC",
        "icon": "al_yousr.png",
        "type": "participatif"
    },
    {
        "name": "BTI Bank",
        "code": "BTI",
        "swift_code": "BTIMAMC",
        "icon": "bti.png",
        "type": "participatif"
    },
    {
        "name": "Assafa Bank",
        "code": "ASB",
        "swift_code": "ASSAFMC",
        "icon": "assafa.png",
        "type": "participatif"
    },
    {
    "name": "Arab Bank Maroc",
    "code": "ARB",
    "swift_code": "ARABMAMC",
    "icon": "arab_bank.png",
    "type": "commercial"
    },
    {
        "name": "Bank Al-Tamweel Wal-Inmaa",
        "code": "BTWI",
        "swift_code": "TAMWMAMC",
        "icon": "btwi.png",
        "type": "participatif"
    },
    {
        "name": "Société Générale Marocaine de Banques",
        "code": "SGMB",
        "swift_code": "SGMBMAMC",
        "icon": "sgmb.png",
        "type": "commercial"
    }
    
]

def check_admin_access():
    """Vérifie si l'utilisateur actuel a un accès admin"""
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('Accès refusé. Seuls les administrateurs peuvent gérer les banques.', 'danger')
        return False
    return True

def allowed_file(filename):
    """Vérifie si l'extension du fichier est autorisée"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_icon_file(file, bank_code=None):
    """Enregistre le fichier icône uploadé et retourne le chemin"""
    if file and allowed_file(file.filename):
        # Crée un nom de fichier unique
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        if bank_code:
            filename = f"{bank_code.lower()}.{file_ext}"
        else:
            filename = f"{uuid.uuid4().hex[:8]}.{file_ext}"
        
        filename = secure_filename(filename)
        
        # Vérifie que le dossier d'upload existe
        upload_dir = os.path.join('static', 'icons', 'banks')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Enregistre le fichier
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        return f"/static/icons/banks/{filename}"
    return None

@banks_bp.route('/')
@login_required
def index():
    banks = Bank.query.order_by(Bank.name).all()
    return render_template('banks/index.html', banks=banks)

@banks_bp.route('/init-moroccan-banks')
@login_required
def init_moroccan_banks():
    """Initialise toutes les banques marocaines"""
    if not check_admin_access():
        return redirect(url_for('banks.index'))
    
    try:
        added = 0
        updated = 0
        
        for bank_data in MOROCCAN_BANKS:
            # Vérifie si la banque existe par code ou nom
            existing_bank = Bank.query.filter(
                (Bank.code == bank_data['code']) | 
                (Bank.name == bank_data['name'])
            ).first()
            
            if not existing_bank:
                bank = Bank(
                    name=bank_data['name'],
                    code=bank_data['code'],
                    swift_code=bank_data['swift_code'],
                    icon_url=f"/static/icons/banks/{bank_data['icon']}",
                    is_active=True
                )
                db.session.add(bank)
                added += 1
            else:
                # Met à jour les informations manquantes
                if not existing_bank.swift_code:
                    existing_bank.swift_code = bank_data['swift_code']
                if not existing_bank.icon_url:
                    existing_bank.icon_url = f"/static/icons/banks/{bank_data['icon']}"
                updated += 1
        
        db.session.commit()
        
        if added > 0 and updated > 0:
            flash(f'{added} nouvelles banques ajoutées et {updated} banques mises à jour.', 'success')
        elif added > 0:
            flash(f'{added} banques marocaines ajoutées avec succès.', 'success')
        elif updated > 0:
            flash(f'{updated} banques mises à jour avec succès.', 'success')
        else:
            flash('Toutes les banques existent déjà.', 'info')
            
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de l'initialisation des banques: {str(e)}", 'danger')
    
    return redirect(url_for('banks.index'))

@banks_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if not check_admin_access():
        return redirect(url_for('banks.index'))
    
    form = BankForm()
    if form.validate_on_submit():
        try:
            # Gère l'upload de l'icône
            icon_url = None
            if 'icon_file' in request.files:
                icon_file = request.files['icon_file']
                if icon_file and icon_file.filename:
                    icon_url = save_icon_file(icon_file, form.code.data)
            
            # Utilise l'URL fournie si aucun fichier n'a été uploadé
            if not icon_url and form.icon_url.data:
                icon_url = form.icon_url.data
            
            bank = Bank(
                name=form.name.data,
                code=form.code.data,
                swift_code=form.swift_code.data,
                icon_url=icon_url,
                is_active=form.is_active.data
            )
            db.session.add(bank)
            db.session.commit()
            flash('Banque ajoutée avec succès!', 'success')
            return redirect(url_for('banks.index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de l'ajout de la banque: {str(e)}", 'danger')
    
    return render_template('banks/form.html', form=form, title='Nouvelle banque')

@banks_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if not check_admin_access():
        return redirect(url_for('banks.index'))
    
    bank = Bank.query.get_or_404(id)
    form = BankForm(obj=bank)
    
    if form.validate_on_submit():
        try:
            # Gère l'upload de l'icône
            if 'icon_file' in request.files:
                icon_file = request.files['icon_file']
                if icon_file and icon_file.filename:
                    # Supprime l'ancienne icône si elle existe
                    if bank.icon_url and bank.icon_url.startswith('/static/icons/banks/'):
                        old_icon_path = bank.icon_url[1:]  # Supprime le slash initial
                        if os.path.exists(old_icon_path):
                            try:
                                os.remove(old_icon_path)
                            except:
                                pass  # Ignore si impossible de supprimer
                    
                    # Enregistre la nouvelle icône
                    new_icon_url = save_icon_file(icon_file, bank.code)
                    if new_icon_url:
                        bank.icon_url = new_icon_url
            
            # Met à jour les autres champs
            bank.name = form.name.data
            bank.code = form.code.data
            bank.swift_code = form.swift_code.data
            bank.is_active = form.is_active.data
            bank.updated_at = datetime.utcnow()
            
            # Met à jour l'URL de l'icône si fournie et aucun fichier uploadé
            if form.icon_url.data and 'icon_file' not in request.files:
                bank.icon_url = form.icon_url.data
            
            db.session.commit()
            flash('Banque modifiée avec succès!', 'success')
            return redirect(url_for('banks.index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la modification: {str(e)}", 'danger')
    
    return render_template('banks/form.html', form=form, title='Modifier la banque', bank=bank)

@banks_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if not check_admin_access():
        return redirect(url_for('banks.index'))
    
    bank = Bank.query.get_or_404(id)
    
    # Vérifie si la banque a des agences avec des chèques
    has_cheques = any(branch.cheques for branch in bank.branches)
    if has_cheques:
        flash('Impossible de supprimer cette banque car elle a des chèques associés.', 'danger')
        return redirect(url_for('banks.index'))
    
    try:
        # Supprime le fichier icône s'il existe
        if bank.icon_url and bank.icon_url.startswith('/static/icons/banks/'):
            icon_path = bank.icon_url[1:]  # Supprime le slash initial
            if os.path.exists(icon_path):
                try:
                    os.remove(icon_path)
                except:
                    pass  # Ignore si impossible de supprimer
        
        # Supprime d'abord toutes les agences
        Branch.query.filter_by(bank_id=id).delete()
        db.session.delete(bank)
        db.session.commit()
        flash('Banque et ses agences supprimées avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression: {str(e)}", 'danger')
    
    return redirect(url_for('banks.index'))

@banks_bp.route('/<int:bank_id>/branches/new', methods=['GET', 'POST'])
@login_required
def new_branch(bank_id):
    if not check_admin_access():
        return redirect(url_for('banks.index'))
    
    bank = Bank.query.get_or_404(bank_id)
    form = BranchForm()
    
    if form.validate_on_submit():
        try:
            branch = Branch(
                bank_id=bank_id,
                name=form.name.data,
                address=form.address.data,
                postal_code=form.postal_code.data,
                phone=form.phone.data,
                email=form.email.data
            )
            db.session.add(branch)
            db.session.commit()
            flash('Agence ajoutée avec succès!', 'success')
            return redirect(url_for('banks.index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de l'ajout de l'agence: {str(e)}", 'danger')
    
    return render_template('banks/branch_form.html', form=form, title=f'Nouvelle agence - {bank.name}', bank=bank)

@banks_bp.route('/branches/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_branch(id):
    if not check_admin_access():
        return redirect(url_for('banks.index'))
    
    branch = Branch.query.get_or_404(id)
    form = BranchForm(obj=branch)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(branch)
            db.session.commit()
            flash('Agence modifiée avec succès!', 'success')
            return redirect(url_for('banks.index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la modification: {str(e)}", 'danger')
    
    return render_template('banks/branch_form.html', form=form, title='Modifier l\'agence', branch=branch)

@banks_bp.route('/branches/<int:id>/delete', methods=['POST'])
@login_required
def delete_branch(id):
    if not check_admin_access():
        return redirect(url_for('banks.index'))
    
    branch = Branch.query.get_or_404(id)
    
    if branch.cheques:
        flash('Impossible de supprimer cette agence car elle a des chèques associés.', 'danger')
        return redirect(url_for('banks.index'))
    
    try:
        db.session.delete(branch)
        db.session.commit()
        flash('Agence supprimée avec succès!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression: {str(e)}", 'danger')
    
    return redirect(url_for('banks.index'))

@banks_bp.route('/api/branches/<int:bank_id>')
@login_required
def api_branches(bank_id):
    """Endpoint API pour obtenir les agences d'une banque spécifique"""
    branches = Branch.query.filter_by(bank_id=bank_id).order_by(Branch.name).all()
    return jsonify([{
        'id': branch.id,
        'name': branch.name,
        'display_name': f"{branch.bank.name} - {branch.name}"
    } for branch in branches])

@banks_bp.route('/api/banks')
@login_required
def api_banks():
    """Endpoint API pour obtenir toutes les banques actives"""
    banks = Bank.query.filter_by(is_active=True).order_by(Bank.name).all()
    return jsonify([{
        'id': bank.id,
        'name': bank.name,
        'code': bank.code,
        'icon_url': bank.icon_url
    } for bank in banks])

@banks_bp.route('/stats')
@login_required
def stats():
    """Statistiques des banques"""
    total_banks = Bank.query.count()
    active_banks = Bank.query.filter_by(is_active=True).count()
    total_branches = Branch.query.count()
    
    # Banques par type (traditionnel/participatif)
    traditional_banks = Bank.query.filter(Bank.name.in_([
        bank['name'] for bank in MOROCCAN_BANKS if bank['type'] == 'commercial'
    ])).count()
    
    islamic_banks = Bank.query.filter(Bank.name.in_([
        bank['name'] for bank in MOROCCAN_BANKS if bank['type'] == 'participatif'
    ])).count()
    
    stats = {
        'total_banks': total_banks,
        'active_banks': active_banks,
        'total_branches': total_branches,
        'traditional_banks': traditional_banks,
        'islamic_banks': islamic_banks
    }
    
    return jsonify(stats)