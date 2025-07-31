from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Bank, Branch, db
from forms import BankForm, BranchForm
from datetime import datetime
import os

banks_bp = Blueprint('banks', __name__)

# List of major Moroccan banks with their details
MOROCCAN_BANKS = [
    {
        "name": "Attijariwafa Bank",
        "code": "AWB",
        "swift_code": "BCMAMAMC",
        "icon": "attijariwafa.png"
    },
    {
        "name": "Banque Populaire",
        "code": "BCP",
        "swift_code": "BCPOMAMC",
        "icon": "banque_populaire.png"
    },
    {
        "name": "BMCE Bank of Africa",
        "code": "BOA",
        "swift_code": "BMCEAMMC",
        "icon": "bmce.png"
    },
    {
        "name": "Crédit Agricole du Maroc",
        "code": "CAM",
        "swift_code": "ACMAMAMC",
        "icon": "credit_agricole.png"
    },
    {
        "name": "CIH Bank",
        "code": "CIH",
        "swift_code": "CIHBMAMC",
        "icon": "cih.png"
    },
    {
        "name": "Société Générale Maroc",
        "code": "SGMB",
        "swift_code": "SGMBMAMC",
        "icon": "societe_generale.png"
    },
    {
        "name": "Al Barid Bank",
        "code": "ABB",
        "swift_code": "BPEIMAMC",
        "icon": "albarid.png"
    }
]

def check_admin_access():
    """Check if current user has admin access"""
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('Accès refusé. Seuls les administrateurs peuvent gérer les banques.', 'danger')
        return False
    return True

@banks_bp.route('/')
@login_required
def index():
    banks = Bank.query.order_by(Bank.name).all()
    return render_template('banks/index.html', banks=banks)

@banks_bp.route('/init-moroccan-banks')
@login_required
def init_moroccan_banks():
    if not check_admin_access():
        return redirect(url_for('banks.index'))
    
    try:
        added = 0
        for bank_data in MOROCCAN_BANKS:
            # Check if bank exists by code or name
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
        
        db.session.commit()
        flash(f'{added} banques marocaines ont été ajoutées avec succès.', 'success')
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
            bank = Bank(
                name=form.name.data,
                code=form.code.data,
                swift_code=form.swift_code.data,
                icon_url=form.icon_url.data,
                is_active=form.is_active.data
            )
            db.session.add(bank)
            db.session.commit()
            flash('Banque ajoutée avec succès!', 'success')
            return redirect(url_for('banks.index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de l'ajout de la banque: {str(e)}", 'danger')
    
    return render_template('banks/form.html', form=form, title='Nouvelle Banque')

@banks_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if not check_admin_access():
        return redirect(url_for('banks.index'))
    
    bank = Bank.query.get_or_404(id)
    form = BankForm(obj=bank)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(bank)
            bank.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Banque modifiée avec succès!', 'success')
            return redirect(url_for('banks.index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la modification: {str(e)}", 'danger')
    
    return render_template('banks/form.html', form=form, title='Modifier Banque', bank=bank)

@banks_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if not check_admin_access():
        return redirect(url_for('banks.index'))
    
    bank = Bank.query.get_or_404(id)
    
    # Check if bank has associated branches with cheques
    has_cheques = any(branch.cheques for branch in bank.branches)
    if has_cheques:
        flash('Impossible de supprimer cette banque car elle contient des chèques associés.', 'danger')
        return redirect(url_for('banks.index'))
    
    try:
        # Delete all branches first
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
    
    return render_template('banks/branch_form.html', form=form, title=f'Nouvelle Agence - {bank.name}', bank=bank)

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
    
    return render_template('banks/branch_form.html', form=form, title='Modifier Agence', branch=branch)

@banks_bp.route('/branches/<int:id>/delete', methods=['POST'])
@login_required
def delete_branch(id):
    if not check_admin_access():
        return redirect(url_for('banks.index'))
    
    branch = Branch.query.get_or_404(id)
    
    if branch.cheques:
        flash('Impossible de supprimer cette agence car elle contient des chèques associés.', 'danger')
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
    """API endpoint to get branches for a specific bank"""
    branches = Branch.query.filter_by(bank_id=bank_id).order_by(Branch.name).all()
    return jsonify([{
        'id': branch.id,
        'name': branch.name,
        'display_name': f"{branch.bank.name} - {branch.name}"
    } for branch in branches])

@banks_bp.route('/api/banks')
@login_required
def api_banks():
    """API endpoint to get all active banks"""
    banks = Bank.query.filter_by(is_active=True).order_by(Bank.name).all()
    return jsonify([{
        'id': bank.id,
        'name': bank.name,
        'code': bank.code,
        'icon_url': bank.icon_url
    } for bank in banks])