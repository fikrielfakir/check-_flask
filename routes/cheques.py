from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import Cheque, Client, Branch, Bank
from forms import ChequeForm
from app import db
from datetime import datetime, date
import os
from utils.excel_manager import ExcelManager

cheques_bp = Blueprint('cheques', __name__)

def check_access():
    """Check if current user has access to manage cheques"""
    if current_user.role not in ['admin', 'comptable', 'agent']:
        flash('Accès refusé.', 'danger')
        return False
    return True

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_duplicate_cheque(cheque_number, branch_id=None, client_id=None):
    """Check if a cheque already exists based on number, branch, and client."""
    query = Cheque.query.filter_by(cheque_number=cheque_number)

    if branch_id:
        query = query.filter_by(branch_id=branch_id)
    if client_id:
        query = query.filter_by(client_id=client_id)

    duplicate_cheque = query.first()

    if duplicate_cheque:
        return True, duplicate_cheque, "Ce numéro de chèque existe déjà."
    return False, None, None


def check_cheque_number_in_branch(cheque_number, branch_id, exclude_id=None):
    """
    Check if cheque number exists in the same branch (different warning level)
    This helps prevent confusion even with different clients
    """
    if not cheque_number or not cheque_number.strip():
        return False, None, None
    
    cheque_number = cheque_number.strip()
    
    query = Cheque.query.filter(
        Cheque.cheque_number == cheque_number,
        Cheque.branch_id == branch_id
    )
    
    if exclude_id:
        query = query.filter(Cheque.id != exclude_id)
    
    existing_cheque = query.first()
    
    if existing_cheque:
        client_name = existing_cheque.client.name if existing_cheque.client else "Client inconnu"
        branch_name = existing_cheque.branch.name if existing_cheque.branch else "Agence inconnue"
        
        warning_message = f'Attention: Le numéro de chèque "{cheque_number}" existe déjà dans cette agence "{branch_name}" pour un autre client "{client_name}". Êtes-vous sûr de vouloir continuer?'
        return True, existing_cheque, warning_message
    
    return False, None, None

@cheques_bp.route('/check-duplicate', methods=['POST'])
@login_required
def check_duplicate_ajax():
    """
    AJAX endpoint to check for duplicates by cheque_number only
    """
    data = request.get_json()
    cheque_number = data.get('cheque_number', '').strip()
    exclude_id = data.get('exclude_id')

    if not cheque_number:
        return jsonify({'is_duplicate': False})

    try:
        if exclude_id:
            exclude_id = int(exclude_id)
    except (ValueError, TypeError):
        exclude_id = None
    
    is_duplicate, duplicate_cheque, error_message = check_duplicate_cheque(
        cheque_number, exclude_id
    )
    
    return jsonify({
        'is_duplicate': bool(is_duplicate),
        'error_message': error_message if is_duplicate else ''
    })

@cheques_bp.route('/')
@login_required
def index():
    # Get filter parameters
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    bank_id = request.args.get('bank_id', '')
    branch_id = request.args.get('branch_id', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Build query
    query = Cheque.query.join(Client).join(Branch).join(Bank)
    
    if search:
        query = query.filter(
            db.or_(
                Cheque.cheque_number.contains(search),
                Client.name.contains(search),
                Bank.name.contains(search)
            )
        )
    
    if status:
        query = query.filter(Cheque.status == status)
    
    if bank_id:
        query = query.filter(Branch.bank_id == bank_id)
    
    if branch_id:
        query = query.filter(Cheque.branch_id == branch_id)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Cheque.due_date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Cheque.due_date <= date_to_obj)
        except ValueError:
            pass
    
    cheques = query.order_by(Cheque.due_date.desc()).all()
    
    # Get banks for filter dropdown
    banks = Bank.query.all()
    branches = Branch.query.all()
    
    return render_template('cheques/index.html', 
                         cheques=cheques,
                         banks=banks,
                         branches=branches,
                         search=search,
                         status=status,
                         bank_id=bank_id,
                         branch_id=branch_id,
                         date_from=date_from,
                         date_to=date_to)

@cheques_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if not check_access():
        return redirect(url_for('cheques.index'))
    
    form = ChequeForm()
    
    if form.validate_on_submit():
        # Enhanced duplicate checking
        is_duplicate, duplicate_cheque, error_message = check_duplicate_cheque(
            form.cheque_number.data,
            form.branch_id.data,
            form.client_id.data
        )
        
        if is_duplicate:
            flash(error_message, 'error')
            return render_template('cheques/form.html', form=form, title='Nouveau Chèque')
        
        # Handle file upload
        scan_path = None
        if form.scan.data:
            file = form.scan.data
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Create unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                scan_path = filename
        
        try:
            cheque = Cheque(
                amount=form.amount.data,
                currency=form.currency.data,
                issue_date=form.issue_date.data,
                due_date=form.due_date.data,
                client_id=form.client_id.data,
                branch_id=form.branch_id.data,
                status=form.status.data,
                cheque_number=form.cheque_number.data.strip() if form.cheque_number.data else None,
                invoice_number=form.invoice_number.data,
                invoice_date=form.invoice_date.data,
                depositor_name=form.depositor_name.data,
                notes=form.notes.data,
                payment_type=form.payment_type.data,
                created_date=form.created_date.data,
                unpaid_reason=form.unpaid_reason.data if form.status.data == 'IMPAYE' else None,
                scan_path=scan_path
            )
            
            db.session.add(cheque)
            db.session.commit()
            
            # Automatically update Excel file
            excel_manager = ExcelManager()
            excel_sync_success = excel_manager.add_or_update_cheque(cheque)
            
            if excel_sync_success:
                flash('Chèque ajouté avec succès et synchronisé avec Excel!', 'success')
            else:
                flash('Chèque ajouté avec succès, mais erreur de synchronisation Excel.', 'warning')
            
            return redirect(url_for('cheques.index'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating cheque: {str(e)}")
            flash('Erreur lors de la création du chèque. Veuillez réessayer.', 'error')
            
            # Clean up uploaded file if it exists
            if scan_path:
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], scan_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
    
    return render_template('cheques/form.html', form=form, title='Nouveau Chèque')

@cheques_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if not check_access():
        return redirect(url_for('cheques.index'))
    
    cheque = Cheque.query.get_or_404(id)
    form = ChequeForm(obj=cheque)
    
    if form.validate_on_submit():
        # Enhanced duplicate checking (excluding current cheque)
        is_duplicate, duplicate_cheque, error_message = check_duplicate_cheque(
            form.cheque_number.data,
            form.branch_id.data,
            form.client_id.data,
            exclude_id=id
        )
        
        if is_duplicate:
            flash(error_message, 'error')
            return render_template('cheques/form.html', form=form, title='Modifier Chèque', cheque=cheque)
        
        # Handle file upload
        if form.scan.data:
            file = form.scan.data
            if file and allowed_file(file.filename):
                # Delete old file if exists
                if cheque.scan_path:
                    old_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], cheque.scan_path)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                cheque.scan_path = filename
        
        try:
            # Update cheque fields
            cheque.amount = form.amount.data
            cheque.currency = form.currency.data
            cheque.issue_date = form.issue_date.data
            cheque.due_date = form.due_date.data
            cheque.client_id = form.client_id.data
            cheque.branch_id = form.branch_id.data
            cheque.status = form.status.data
            cheque.cheque_number = form.cheque_number.data.strip() if form.cheque_number.data else None
            cheque.invoice_number = form.invoice_number.data
            cheque.invoice_date = form.invoice_date.data
            cheque.depositor_name = form.depositor_name.data
            cheque.notes = form.notes.data
            cheque.payment_type = form.payment_type.data
            cheque.created_date = form.created_date.data
            cheque.unpaid_reason = form.unpaid_reason.data if form.status.data == 'IMPAYE' else None
            cheque.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Automatically update Excel file
            excel_manager = ExcelManager()
            excel_sync_success = excel_manager.add_or_update_cheque(cheque)
            
            if excel_sync_success:
                flash('Chèque modifié avec succès et synchronisé avec Excel!', 'success')
            else:
                flash('Chèque modifié avec succès, mais erreur de synchronisation Excel.', 'warning')
            
            return redirect(url_for('cheques.index'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating cheque: {str(e)}")
            flash('Erreur lors de la modification du chèque. Veuillez réessayer.', 'error')
    
    return render_template('cheques/form.html', form=form, title='Modifier Chèque', cheque=cheque)

@cheques_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if current_user.role != 'admin':
        flash('Seuls les administrateurs peuvent supprimer des chèques.', 'danger')
        return redirect(url_for('cheques.index'))
    
    cheque = Cheque.query.get_or_404(id)
    
    try:
        # Delete scan file if exists
        if cheque.scan_path:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], cheque.scan_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # Remove from Excel before deleting from database
        excel_manager = ExcelManager()
        if cheque.cheque_number and cheque.branch:
            excel_manager.remove_cheque_from_excel(
                cheque.cheque_number, 
                cheque.branch.bank.name,
                cheque.due_date.year
            )
        
        db.session.delete(cheque)
        db.session.commit()
        flash('Chèque supprimé avec succès!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting cheque: {str(e)}")
        flash('Erreur lors de la suppression du chèque.', 'error')
    
    return redirect(url_for('cheques.index'))

@cheques_bp.route('/<int:id>/update-status', methods=['POST'])
@login_required
def update_status(id):
    if not check_access():
        return redirect(url_for('cheques.index'))

    cheque = Cheque.query.get_or_404(id)
    new_status = request.form.get('status')

    current_app.logger.info(f"Submitted status: {new_status}")

    # Normalization map
    status_map = {
        'en_attente': 'EN ATTENTE',
        'encaisse': 'ENCAISSE',
        'impaye': 'IMPAYE'
    }

    # Normalize status input
    normalized_status = status_map.get(new_status.strip().lower()) if new_status else None

    if normalized_status:
        try:
            cheque.status = normalized_status
            cheque.updated_at = datetime.utcnow()
            db.session.commit()

            # Automatically update Excel file
            excel_manager = ExcelManager()
            excel_sync_success = excel_manager.add_or_update_cheque(cheque)
            
            if excel_sync_success:
                flash(f'Statut du chèque mis à jour et synchronisé avec Excel: {cheque.status_text}', 'success')
            else:
                flash(f'Statut du chèque mis à jour: {cheque.status_text} (Erreur sync Excel)', 'warning')
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating cheque status: {str(e)}")
            flash('Erreur lors de la mise à jour du statut.', 'error')
    else:
        flash('Statut invalide.', 'danger')

    return redirect(url_for('cheques.index'))