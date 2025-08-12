from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import (Cheque, Client, Branch, Bank, ChequeStatusHistory,Depositor,
                   ChequeRetryAttempt, ChequeLegalAction, ImpayeNotification, STANDARD_REJECTION_REASONS)
from forms import (ChequeForm, ImpayeStatusForm, RetryAttemptForm, RetryResultForm,
                  AlternativePaymentForm, LegalActionForm, NotificationForm, PresentationForm)
from app import db
from datetime import datetime, date, timedelta
from utils.enhanced_excel_sync import EnhancedExcelSync
import os
import re
from pathlib import Path

cheques_bp = Blueprint('cheques', __name__)

def check_access():
    """Check if current user has access to manage cheques"""
    if current_user.role not in ['admin', 'comptable', 'agent']:
        flash('Accès refusé.', 'danger')
        return False
    return True

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_duplicate_cheque(cheque_number, branch_id=None, client_id=None, exclude_id=None):
    """
    Enhanced cheque duplication check with additional validation
    
    Args:
        cheque_number: The cheque number to check
        branch_id: Optional branch ID to scope the check
        client_id: Optional client ID to scope the check
        exclude_id: Optional cheque ID to exclude (for updates)
    
    Returns:
        tuple: (is_duplicate, duplicate_cheque, error_message)
    """
    if not cheque_number or not isinstance(cheque_number, str):
        return False, None, None
    
    cheque_number = cheque_number.strip()
    
    # Validate cheque number format
    if not re.match(r'^[A-Z0-9]{6,20}$', cheque_number):
        return False, None, "Format de numéro de chèque invalide (6-20 caractères alphanumériques)"
    
    # Build the query step by step
    query = Cheque.query.filter(Cheque.cheque_number == cheque_number)
    
    # Add filters if provided
    if branch_id:
        query = query.filter(Cheque.branch_id == branch_id)
    if client_id:
        query = query.filter(Cheque.client_id == client_id)
    
    # Exclude the current cheque if editing
    if exclude_id:
        query = query.filter(Cheque.id != exclude_id)

    duplicate_cheque = query.first()

    if duplicate_cheque:
        client_name = duplicate_cheque.client.name if duplicate_cheque.client else "Client inconnu"
        branch_name = duplicate_cheque.branch.name if duplicate_cheque.branch else "Agence inconnue"
        
        error_message = f'Ce numéro de chèque "{cheque_number}" existe déjà pour le client "{client_name}" dans l\'agence "{branch_name}".'
        return True, duplicate_cheque, error_message
    
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
    AJAX endpoint to check for duplicates
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'is_duplicate': False, 'has_warning': False})
        
        cheque_number = data.get('cheque_number', '').strip()
        branch_id = data.get('branch_id')
        client_id = data.get('client_id')
        exclude_id = data.get('exclude_id')

        # Validate input
        if not cheque_number:
            return jsonify({'is_duplicate': False, 'has_warning': False})

        # Convert IDs to integers
        try:
            branch_id = int(branch_id) if branch_id else None
            client_id = int(client_id) if client_id else None
            exclude_id = int(exclude_id) if exclude_id else None
        except (ValueError, TypeError):
            return jsonify({'is_duplicate': False, 'has_warning': False, 
                           'error': 'IDs invalides'})
        
        # First check: Exact duplicate (same cheque number, branch, and client)
        is_duplicate, duplicate_cheque, error_message = check_duplicate_cheque(
            cheque_number, branch_id, client_id, exclude_id
        )
        
        if is_duplicate:
            return jsonify({
                'is_duplicate': True,
                'has_warning': False,
                'error_message': error_message
            })
        
        # Second check: Same cheque number in same branch but different client (warning)
        if branch_id and client_id:
            has_warning, warning_cheque, warning_message = check_cheque_number_in_branch(
                cheque_number, branch_id, exclude_id
            )
            
            # Only show warning if it's a different client
            if has_warning and warning_cheque.client_id != client_id:
                return jsonify({
                    'is_duplicate': False,
                    'has_warning': True,
                    'warning_message': warning_message
                })
        
        # No duplicates or warnings found
        return jsonify({
            'is_duplicate': False,
            'has_warning': False
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in duplicate check: {str(e)}")
        return jsonify({
            'is_duplicate': False,
            'has_warning': False,
            'error': 'Erreur lors de la vérification'
        }), 500

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
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('CHEQUES_PER_PAGE', 20)
    
    # Build query with explicit joins
    query = db.session.query(Cheque).join(
        Client, Cheque.client_id == Client.id
    ).join(
        Branch, Cheque.branch_id == Branch.id
    ).join(
        Bank, Branch.bank_id == Bank.id
    )
    
    # Apply filters
    if search:
        query = query.filter(db.or_(
            Cheque.cheque_number.contains(search),
            Client.name.contains(search),
            Depositor.name.contains(search),
            Bank.name.contains(search)
        ))
    
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
    
    # Get counts for statistics - using the same filtered query
    total_count = query.count()
    pending_count = query.filter(Cheque.status == 'EN ATTENTE').count()
    paid_count = query.filter(Cheque.status == 'ENCAISSE').count()
    unpaid_count = query.filter(Cheque.status == 'IMPAYE').count()
    
    # Paginate results
    cheques = query.order_by(Cheque.due_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    # Get banks and branches for dropdowns
    banks = Bank.query.order_by(Bank.name).all()
    branches = Branch.query.order_by(Branch.name).all()
    
    return render_template('cheques/index.html',
                         cheques=cheques,
                         banks=banks,
                         branches=branches,
                         search=search,
                         status=status,
                         bank_id=bank_id,
                         branch_id=branch_id,
                         date_from=date_from,
                         date_to=date_to,
                         date=date,
                         counts={
                             'total': total_count,
                             'pending': pending_count,
                             'paid': paid_count,
                             'unpaid': unpaid_count
                         })
                         
# Updated new and edit routes to use enhanced duplicate prevention
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
            form.client_id.data,
            exclude_id=None  # No exclusion for new cheques
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
                depositor_id=form.depositor_id.data if form.depositor_id.data and form.depositor_id.data != 0 else None,
                branch_id=form.branch_id.data,
                deposit_branch_id=form.deposit_branch_id.data if form.deposit_branch_id.data and form.deposit_branch_id.data != 0 else None,
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
            
            # Use ENHANCED Excel sync with COMPREHENSIVE duplicate prevention
            excel_folder = Path(current_app.config.get('EXCEL_FOLDER', 'data/excel'))
            enhanced_sync = EnhancedExcelSync(excel_folder)
            excel_sync_success = enhanced_sync.sync_cheque(cheque, 'create')
            
            if excel_sync_success:
                flash('Chèque ajouté avec succès et synchronisé avec Excel (doublons automatiquement supprimés)!', 'success')
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
        # Only check duplicates if cheque number has changed
        if form.cheque_number.data != cheque.cheque_number:
            is_duplicate, duplicate_cheque, error_message = check_duplicate_cheque(
                form.cheque_number.data,
                form.branch_id.data,
                form.client_id.data,
                exclude_id=cheque.id  # Exclude current cheque
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
            cheque.depositor_id = form.depositor_id.data if form.depositor_id.data and form.depositor_id.data != 0 else None
            cheque.branch_id = form.branch_id.data
            cheque.deposit_branch_id = form.deposit_branch_id.data if form.deposit_branch_id.data and form.deposit_branch_id.data != 0 else None
            cheque.status = form.status.data
            # Update cheque number if changed
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
            
            # Use ENHANCED Excel sync with COMPREHENSIVE duplicate prevention
            excel_folder = Path(current_app.config.get('EXCEL_FOLDER', 'data/excel'))
            enhanced_sync = EnhancedExcelSync(excel_folder)
            excel_sync_success = enhanced_sync.sync_cheque(cheque, 'update')
            
            if excel_sync_success:
                flash('Chèque modifié avec succès et synchronisé avec Excel (doublons automatiquement supprimés)!', 'success')
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
        
        # Remove from Excel before deleting from database with enhanced sync
        excel_folder = Path(current_app.config.get('EXCEL_FOLDER', 'data/excel'))
        enhanced_sync = EnhancedExcelSync(excel_folder)
        enhanced_sync.sync_cheque(cheque, 'delete')
        
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
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('cheques.index'))

    try:
        cheque = Cheque.query.get_or_404(id)
        new_status = request.form.get('status', '').strip().upper()
        
        current_app.logger.info(f"Status update requested for cheque {id}: {new_status}")

        # Define valid status transitions
        valid_statuses = {
            'EN_ATTENTE': 'EN ATTENTE',
            'ENCAISSE': 'ENCAISSE', 
            'IMPAYE': 'IMPAYE',
            'DEPOSE': 'DÉPOSÉ',
            'ANNULE': 'ANNULÉ',
            'PRESENTE': 'PRÉSENTÉ',
            'TENTATIVE': 'TENTATIVE',
            'PROCEDURE': 'PROCÉDURE',
            'RECOUVRE': 'RECOUVRÉ'
        }

        # Validate status
        if new_status not in valid_statuses:
            flash('Statut invalide', 'danger')
            current_app.logger.error(f"Invalid status provided: {new_status}")
            return redirect(url_for('cheques.index'))

        # Record status change history before updating
        status_history = ChequeStatusHistory(
            cheque_id=cheque.id,
            old_status=cheque.status,
            new_status=new_status,
            changed_by=current_user.id,
            notes=f"Changement de statut via l'interface"
        )
        db.session.add(status_history)

        # Update cheque status
        cheque.status = new_status
        cheque.updated_at = datetime.utcnow()
        
        # Handle special status cases
        if new_status == 'IMPAYE':
            cheque.rejection_date = datetime.utcnow().date()
        elif new_status == 'ENCAISSE':
            cheque.clearance_date = datetime.utcnow().date()
        elif new_status == 'PRESENTE':
            cheque.presentation_date = datetime.utcnow().date()
        elif new_status == 'DEPOSE':
            cheque.deposit_date = datetime.utcnow().date()

        db.session.commit()
        current_app.logger.info(f"Cheque {id} status updated to {new_status}")

        # Enhanced Excel synchronization with proper error handling
        try:
            excel_folder = Path(current_app.config.get('EXCEL_FOLDER', 'data/excel'))
            enhanced_sync = EnhancedExcelSync(excel_folder)
            sync_result = enhanced_sync.sync_cheque(cheque, 'update')
            
            if not sync_result:
                current_app.logger.warning(f"Excel sync failed for cheque {id}")
                flash(f"Statut mis à jour mais échec de synchronisation Excel", 'warning')
            else:
                flash(f"Statut mis à jour avec succès: {valid_statuses[new_status]}", 'success')
                
        except Exception as e:
            current_app.logger.error(f"Excel sync error for cheque {id}: {str(e)}", exc_info=True)
            flash(f"Statut mis à jour mais erreur de synchronisation Excel", 'warning')

        return redirect(url_for('cheques.index'))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating status for cheque {id}: {str(e)}", exc_info=True)
        flash('Erreur technique lors de la mise à jour du statut', 'danger')
        return redirect(url_for('cheques.index'))

# Enhanced Impayé Management Routes
@cheques_bp.route('/<int:id>/present', methods=['GET', 'POST'])
@login_required
def present_cheque(id):
    """Mark cheque as presented for collection"""
    if not check_access():
        return redirect(url_for('cheques.index'))
    
    cheque = Cheque.query.get_or_404(id)
    form = PresentationForm()
    
    if form.validate_on_submit():
        try:
            # Record status change history
            status_history = ChequeStatusHistory(
                cheque_id=cheque.id,
                old_status=cheque.status,
                new_status='PRESENTE',
                changed_by=current_user.id,
                notes=f"Chèque présenté pour encaissement le {form.presentation_date.data}"
            )
            db.session.add(status_history)
            
            # Update cheque
            cheque.status = 'PRESENTE'
            cheque.presentation_date = form.presentation_date.data
            cheque.notes = (cheque.notes or '') + f"\n\nPrésenté le {form.presentation_date.data}: {form.notes.data or ''}"
            cheque.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Sync with Excel
            excel_folder = Path(current_app.config.get('EXCEL_FOLDER', 'data/excel'))
            enhanced_sync = EnhancedExcelSync(excel_folder)
            enhanced_sync.sync_cheque(cheque, 'update')
            
            flash('Chèque marqué comme présenté avec succès!', 'success')
            return redirect(url_for('cheques.index'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error presenting cheque {id}: {str(e)}")
            flash('Erreur lors de la présentation du chèque', 'danger')
    
    return render_template('cheques/present_form.html', form=form, cheque=cheque)

@cheques_bp.route('/<int:id>/impaye', methods=['GET', 'POST'])
@login_required
def mark_impaye(id):
    """Mark cheque as Impayé (bounced) with rejection details"""
    if not check_access():
        return redirect(url_for('cheques.index'))
    
    cheque = Cheque.query.get_or_404(id)
    form = ImpayeStatusForm()
    
    if form.validate_on_submit():
        try:
            # Handle rejection notice upload
            rejection_notice_path = None
            if form.rejection_notice.data:
                file = form.rejection_notice.data
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"rejection_{timestamp}_{filename}"
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    rejection_notice_path = filename
            
            # Record status change history
            status_history = ChequeStatusHistory(
                cheque_id=cheque.id,
                old_status=cheque.status,
                new_status='IMPAYE',
                changed_by=current_user.id,
                notes=f"Chèque rejeté - Motif: {form.rejection_reason.data}"
            )
            db.session.add(status_history)
            
            # Update cheque
            cheque.status = 'IMPAYE'
            cheque.rejection_date = form.rejection_date.data
            cheque.rejection_reason = form.rejection_reason.data
            cheque.rejection_notice_path = rejection_notice_path
            cheque.unpaid_reason = form.notes.data
            cheque.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Sync with Excel
            excel_folder = Path(current_app.config.get('EXCEL_FOLDER', 'data/excel'))
            enhanced_sync = EnhancedExcelSync(excel_folder)
            enhanced_sync.sync_cheque(cheque, 'update')
            
            flash('Chèque marqué comme impayé avec succès!', 'success')
            return redirect(url_for('cheques.index'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error marking cheque as impayé {id}: {str(e)}")
            flash('Erreur lors du marquage comme impayé', 'danger')
    
    return render_template('cheques/impaye_form.html', form=form, cheque=cheque)

@cheques_bp.route('/<int:id>/schedule-retry', methods=['GET', 'POST'])
@login_required
def schedule_retry(id):
    """Schedule a retry attempt for a bounced cheque"""
    if not check_access():
        return redirect(url_for('cheques.index'))
    
    cheque = Cheque.query.get_or_404(id)
    form = RetryAttemptForm()
    
    if form.validate_on_submit():
        try:
            # Count existing retry attempts
            retry_count = ChequeRetryAttempt.query.filter_by(cheque_id=cheque.id).count()
            
            # Create retry attempt
            retry_attempt = ChequeRetryAttempt(
                cheque_id=cheque.id,
                attempt_number=retry_count + 1,
                scheduled_date=form.scheduled_date.data,
                status='scheduled',
                notes=form.notes.data,
                created_by=current_user.id
            )
            db.session.add(retry_attempt)
            
            # Update cheque
            cheque.retry_count = retry_count + 1
            cheque.next_retry_date = form.scheduled_date.data
            cheque.status = 'TENTATIVE'
            cheque.updated_at = datetime.utcnow()
            
            # Record status change
            status_history = ChequeStatusHistory(
                cheque_id=cheque.id,
                old_status=cheque.status,
                new_status='TENTATIVE',
                changed_by=current_user.id,
                notes=f"Tentative #{retry_count + 1} programmée pour le {form.scheduled_date.data}"
            )
            db.session.add(status_history)
            
            db.session.commit()
            
            # Sync with Excel
            excel_folder = Path(current_app.config.get('EXCEL_FOLDER', 'data/excel'))
            enhanced_sync = EnhancedExcelSync(excel_folder)
            enhanced_sync.sync_cheque(cheque, 'update')
            
            flash('Tentative de recouvrement programmée avec succès!', 'success')
            return redirect(url_for('cheques.index'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error scheduling retry for cheque {id}: {str(e)}")
            flash('Erreur lors de la programmation de la tentative', 'danger')
    
    return render_template('cheques/retry_form.html', form=form, cheque=cheque)

@cheques_bp.route('/<int:id>/alternative-payment', methods=['GET', 'POST'])
@login_required
def record_alternative_payment(id):
    """Record alternative payment received for a bounced cheque"""
    if not check_access():
        return redirect(url_for('cheques.index'))
    
    cheque = Cheque.query.get_or_404(id)
    form = AlternativePaymentForm()
    
    if form.validate_on_submit():
        try:
            # Update cheque
            cheque.status = 'RECOUVRE'
            cheque.recovery_method = form.recovery_method.data
            cheque.recovery_date = form.recovery_date.data
            cheque.recovery_amount = form.recovery_amount.data
            cheque.notes = (cheque.notes or '') + f"\n\nRecouvré le {form.recovery_date.data} par {form.recovery_method.data}: {form.recovery_amount.data} MAD"
            cheque.updated_at = datetime.utcnow()
            
            # Record status change
            status_history = ChequeStatusHistory(
                cheque_id=cheque.id,
                old_status=cheque.status,
                new_status='RECOUVRE',
                changed_by=current_user.id,
                notes=f"Recouvrement alternatif: {form.recovery_method.data} - {form.recovery_amount.data} MAD"
            )
            db.session.add(status_history)
            
            db.session.commit()
            
            # Sync with Excel
            excel_folder = Path(current_app.config.get('EXCEL_FOLDER', 'data/excel'))
            enhanced_sync = EnhancedExcelSync(excel_folder)
            enhanced_sync.sync_cheque(cheque, 'update')
            
            flash('Paiement alternatif enregistré avec succès!', 'success')
            return redirect(url_for('cheques.index'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error recording alternative payment for cheque {id}: {str(e)}")
            flash('Erreur lors de l\'enregistrement du paiement alternatif', 'danger')
    
    return render_template('cheques/alternative_payment_form.html', form=form, cheque=cheque)

@cheques_bp.route('/<int:id>/legal-action', methods=['GET', 'POST'])
@login_required
def initiate_legal_action(id):
    """Initiate legal action for a bounced cheque"""
    if not check_access():
        return redirect(url_for('cheques.index'))
    
    cheque = Cheque.query.get_or_404(id)
    
    # Check if cheque is eligible for legal action
    if cheque.status not in ['IMPAYE', 'TENTATIVE']:
        flash('Seuls les chèques impayés peuvent faire l\'objet d\'une action légale.', 'error')
        return redirect(url_for('cheques.index'))
    
    form = LegalActionForm()
    
    if form.validate_on_submit():
        try:
            # Handle legal documents upload
            documents_path = None
            if form.legal_documents.data:
                file = form.legal_documents.data
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"legal_{timestamp}_{filename}"
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    documents_path = filename
            
            # Create legal action record
            legal_action = ChequeLegalAction(
                cheque_id=cheque.id,
                action_type=form.action_type.data,
                status='initiated',
                file_reference=form.file_reference.data,
                court_reference=form.court_reference.data,
                lawyer_name=form.lawyer_name.data,
                lawyer_contact=form.lawyer_contact.data,
                initiated_date=form.initiated_date.data,
                deadline_date=form.deadline_date.data,
                amount_claimed=form.amount_claimed.data,
                court_fees=form.court_fees.data,
                lawyer_fees=form.lawyer_fees.data,
                notes=form.notes.data,
                documents_path=documents_path,
                created_by=current_user.id
            )
            db.session.add(legal_action)
            
            # Update cheque
            cheque.status = 'PROCEDURE'
            cheque.legal_action_initiated = True
            cheque.legal_file_reference = form.file_reference.data
            cheque.court_case_reference = form.court_reference.data
            cheque.lawyer_name = form.lawyer_name.data
            cheque.legal_notes = form.notes.data
            cheque.updated_at = datetime.utcnow()
            
            # Record status change
            status_history = ChequeStatusHistory(
                cheque_id=cheque.id,
                old_status=cheque.status,
                new_status='PROCEDURE',
                changed_by=current_user.id,
                notes=f"Action légale initiée: {form.action_type.data}"
            )
            db.session.add(status_history)
            
            db.session.commit()
            
            # Sync with Excel
            excel_folder = Path(current_app.config.get('EXCEL_FOLDER', 'data/excel'))
            enhanced_sync = EnhancedExcelSync(excel_folder)
            enhanced_sync.sync_cheque(cheque, 'update')
            
            flash('Action légale initiée avec succès!', 'success')
            return redirect(url_for('cheques.index'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error initiating legal action for cheque {id}: {str(e)}")
            flash('Erreur lors de l\'initiation de l\'action légale', 'danger')
    
    return render_template('cheques/legal_action_form.html', form=form, cheque=cheque)

@cheques_bp.route('/<int:id>/impaye-details')
@login_required
def impaye_details(id):
    """View detailed information about an impayé cheque"""
    cheque = Cheque.query.get_or_404(id)
    
    # Get related data
    retry_attempts = ChequeRetryAttempt.query.filter_by(cheque_id=id).order_by(ChequeRetryAttempt.created_at.desc()).all()
    legal_actions = ChequeLegalAction.query.filter_by(cheque_id=id).order_by(ChequeLegalAction.created_at.desc()).all()
    notifications = ImpayeNotification.query.filter_by(cheque_id=id).order_by(ImpayeNotification.sent_date.desc()).all()
    status_history = ChequeStatusHistory.query.filter_by(cheque_id=id).order_by(ChequeStatusHistory.changed_at.desc()).all()
    
    return render_template('cheques/impaye_details.html', 
                         cheque=cheque,
                         retry_attempts=retry_attempts,
                         legal_actions=legal_actions,
                         notifications=notifications,
                         status_history=status_history,
                         rejection_reasons=dict((r['code'], r['reason_fr']) for r in STANDARD_REJECTION_REASONS))

@cheques_bp.route('/impaye-dashboard')
@login_required
def impaye_dashboard():
    """Dashboard showing all impayé cheques and statistics"""
    # Get impayé cheques
    impaye_cheques = Cheque.query.filter(Cheque.status.in_(['IMPAYE', 'TENTATIVE', 'PROCEDURE'])).all()
    
    # Calculate statistics
    total_impaye = len(impaye_cheques)
    total_amount = sum(cheque.amount for cheque in impaye_cheques)
    
    # Group by status
    status_stats = {}
    for cheque in impaye_cheques:
        status = cheque.status
        if status not in status_stats:
            status_stats[status] = {'count': 0, 'amount': 0}
        status_stats[status]['count'] += 1
        status_stats[status]['amount'] += cheque.amount
    
    # Get upcoming retry attempts
    upcoming_retries = ChequeRetryAttempt.query.filter(
        ChequeRetryAttempt.status == 'scheduled',
        ChequeRetryAttempt.scheduled_date <= date.today() + timedelta(days=7)
    ).order_by(ChequeRetryAttempt.scheduled_date).all()
    
    return render_template('cheques/impaye_dashboard.html',
                         impaye_cheques=impaye_cheques,
                         total_impaye=total_impaye,
                         total_amount=total_amount,
                         status_stats=status_stats,
                         upcoming_retries=upcoming_retries,
                         date=date)

# Excel Management Routes
@cheques_bp.route('/excel/cleanup-duplicates')
@login_required
def cleanup_excel_duplicates():
    """Clean up duplicate entries in Excel files - COMPREHENSIVE VERSION"""
    if current_user.role != 'admin':
        flash('Seuls les administrateurs peuvent nettoyer les doublons Excel.', 'danger')
        return redirect(url_for('cheques.index'))
    
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        excel_folder = Path(current_app.config.get('EXCEL_FOLDER', 'data/excel'))
        enhanced_sync = EnhancedExcelSync(excel_folder)
        
        # Use the comprehensive duplicate removal method
        results = enhanced_sync.remove_all_duplicates_comprehensive(year)
        
        if results.get('status') == 'error':
            flash(f"Erreur lors du nettoyage: {results['message']}", 'danger')
        elif results.get('status') == 'no_file':
            flash(results['message'], 'info')
        else:
            if results['duplicates_removed'] > 0:
                flash(f"Nettoyage terminé: {results['duplicates_removed']} doublons supprimés sur {results['duplicates_found']} trouvés dans {results['sheets_processed']} feuilles.", 'success')
            else:
                flash('Aucun doublon trouvé.', 'info')
            
            if results['errors']:
                flash(f"Quelques erreurs rencontrées: {'; '.join(results['errors'][:3])}", 'warning')
        
    except Exception as e:
        current_app.logger.error(f"Error in cleanup duplicates: {str(e)}")
        flash('Erreur technique lors du nettoyage.', 'danger')
    
    return redirect(url_for('cheques.index'))

@cheques_bp.route('/excel/verify-integrity')
@login_required
def verify_excel_integrity():
    """Verify integrity between database and Excel files - ENHANCED VERSION"""
    if current_user.role not in ['admin', 'comptable']:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('cheques.index'))
    
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        excel_folder = Path(current_app.config.get('EXCEL_FOLDER', 'data/excel'))
        enhanced_sync = EnhancedExcelSync(excel_folder)
        
        integrity_report = enhanced_sync.verify_integrity_comprehensive(year)
        
        if 'error' in integrity_report:
            flash(f"Erreur lors de la vérification: {integrity_report['error']}", 'danger')
        else:
            if integrity_report['has_duplicates']:
                flash(f"⚠️ DOUBLONS DÉTECTÉS pour {year}: {integrity_report['excel_duplicates_count']} doublons trouvés dans Excel!", 'warning')
            
            if integrity_report['in_sync'] and not integrity_report['has_duplicates']:
                flash(f"✅ Intégrité vérifiée pour {year}: Tout est synchronisé et sans doublons!", 'success')
            else:
                message_parts = [f"Rapport d'intégrité pour {year}:"]
                message_parts.append(f"- Base de données: {integrity_report['database_count']} chèques")
                message_parts.append(f"- Mappings: {integrity_report['mapping_count']}")
                message_parts.append(f"- Excel total: {integrity_report['excel_count']} entrées")
                message_parts.append(f"- Excel unique: {integrity_report['excel_unique_count']} entrées")
                
                if integrity_report['has_duplicates']:
                    message_parts.append(f"- ⚠️ Doublons Excel: {integrity_report['excel_duplicates_count']}")
                
                flash('\n'.join(message_parts), 'warning')
        
    except Exception as e:
        current_app.logger.error(f"Error in verify integrity: {str(e)}")
        flash('Erreur technique lors de la vérification.', 'danger')
    
    return redirect(url_for('cheques.index'))

@cheques_bp.route('/excel/force-clean-duplicates')
@login_required
def force_clean_all_duplicates():
    """Force clean ALL duplicates across all years"""
    if current_user.role != 'admin':
        flash('Seuls les administrateurs peuvent effectuer cette opération.', 'danger')
        return redirect(url_for('cheques.index'))
    
    try:
        excel_folder = Path(current_app.config.get('EXCEL_FOLDER', 'data/excel'))
        enhanced_sync = EnhancedExcelSync(excel_folder)
        
        total_removed = 0
        total_found = 0
        years_processed = 0
        
        # Process all Excel files in the folder
        for excel_file in excel_folder.glob('cheques_*.xlsx'):
            try:
                # Extract year from filename
                year_match = re.search(r'cheques_(\d{4})\.xlsx', excel_file.name)
                if year_match:
                    year = int(year_match.group(1))
                    current_app.logger.info(f"Processing duplicates for year {year}")
                    
                    results = enhanced_sync.remove_all_duplicates_comprehensive(year)
                    
                    if results.get('status') not in ['error', 'no_file']:
                        total_removed += results['duplicates_removed']
                        total_found += results['duplicates_found']
                        years_processed += 1
                        
            except Exception as e:
                current_app.logger.error(f"Error processing file {excel_file}: {str(e)}")
                continue
        
        if total_removed > 0:
            flash(f"Nettoyage force terminé: {total_removed} doublons supprimés sur {total_found} trouvés dans {years_processed} années.", 'success')
        else:
            flash(f"Aucun doublon trouvé dans les {years_processed} années vérifiées.", 'info')
        
    except Exception as e:
        current_app.logger.error(f"Error in force clean duplicates: {str(e)}")
        flash('Erreur technique lors du nettoyage forcé.', 'danger')
    
    return redirect(url_for('cheques.index'))