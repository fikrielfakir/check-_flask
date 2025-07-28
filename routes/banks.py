from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Bank, Branch
from forms import BankForm, BranchForm
from app import db

banks_bp = Blueprint('banks', __name__)

def check_admin_access():
    """Check if current user has admin access"""
    if current_user.role not in ['admin']:
        flash('Accès refusé. Seuls les administrateurs peuvent gérer les banques.', 'danger')
        return False
    return True

@banks_bp.route('/')
@login_required
def index():
    banks = Bank.query.all()
    return render_template('banks/index.html', banks=banks)

@banks_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if not check_admin_access():
        return redirect(url_for('banks.index'))
    
    form = BankForm()
    if form.validate_on_submit():
        bank = Bank(name=form.name.data)
        db.session.add(bank)
        db.session.commit()
        flash('Banque ajoutée avec succès!', 'success')
        return redirect(url_for('banks.index'))
    
    return render_template('banks/form.html', form=form, title='Nouvelle Banque')

@banks_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if not check_admin_access():
        return redirect(url_for('banks.index'))
    
    bank = Bank.query.get_or_404(id)
    form = BankForm(obj=bank)
    
    if form.validate_on_submit():
        bank.name = form.name.data
        db.session.commit()
        flash('Banque modifiée avec succès!', 'success')
        return redirect(url_for('banks.index'))
    
    return render_template('banks/form.html', form=form, title='Modifier Banque', bank=bank)

@banks_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if not check_admin_access():
        return redirect(url_for('banks.index'))
    
    bank = Bank.query.get_or_404(id)
    
    # Check if bank has associated cheques
    if bank.branches:
        for branch in bank.branches:
            if branch.cheques:
                flash('Impossible de supprimer cette banque car elle contient des chèques.', 'danger')
                return redirect(url_for('banks.index'))
    
    db.session.delete(bank)
    db.session.commit()
    flash('Banque supprimée avec succès!', 'success')
    return redirect(url_for('banks.index'))

@banks_bp.route('/<int:bank_id>/branches/new', methods=['GET', 'POST'])
@login_required
def new_branch(bank_id):
    if not check_admin_access():
        return redirect(url_for('banks.index'))
    
    bank = Bank.query.get_or_404(bank_id)
    form = BranchForm()
    
    if form.validate_on_submit():
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
    
    return render_template('banks/form.html', form=form, title=f'Nouvelle Agence - {bank.name}', bank=bank)

@banks_bp.route('/branches/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_branch(id):
    if not check_admin_access():
        return redirect(url_for('banks.index'))
    
    branch = Branch.query.get_or_404(id)
    form = BranchForm(obj=branch)
    
    if form.validate_on_submit():
        branch.name = form.name.data
        branch.address = form.address.data
        branch.postal_code = form.postal_code.data
        branch.phone = form.phone.data
        branch.email = form.email.data
        db.session.commit()
        flash('Agence modifiée avec succès!', 'success')
        return redirect(url_for('banks.index'))
    
    return render_template('banks/form.html', form=form, title='Modifier Agence', branch=branch)

@banks_bp.route('/branches/<int:id>/delete', methods=['POST'])
@login_required
def delete_branch(id):
    if not check_admin_access():
        return redirect(url_for('banks.index'))
    
    branch = Branch.query.get_or_404(id)
    
    # Check if branch has associated cheques
    if branch.cheques:
        flash('Impossible de supprimer cette agence car elle contient des chèques.', 'danger')
        return redirect(url_for('banks.index'))
    
    db.session.delete(branch)
    db.session.commit()
    flash('Agence supprimée avec succès!', 'success')
    return redirect(url_for('banks.index'))

@banks_bp.route('/api/branches/<int:bank_id>')
@login_required
def api_branches(bank_id):
    """API endpoint to get branches for a specific bank"""
    branches = Branch.query.filter_by(bank_id=bank_id).all()
    return jsonify([{
        'id': branch.id,
        'name': branch.name,
        'display_name': branch.display_name
    } for branch in branches])
