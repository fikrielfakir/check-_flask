from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import (Cheque, Client, Branch, Bank, ChequeStatusHistory, 
                   ChequeRetryAttempt, ChequeLegalAction, ImpayeNotification, STANDARD_REJECTION_REASONS)
from forms import (ChequeForm, ImpayeStatusForm, RetryAttemptForm, RetryResultForm,
                  AlternativePaymentForm, LegalActionForm, NotificationForm, PresentationForm)
from app import db
from datetime import datetime, date, timedelta

import os
from utils.excel_manager import ExcelManager
from utils.optimized_excel_sync import OptimizedExcelSync
from utils.auto_sheet_creator import AutoSheetCreator
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
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx'}
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
    
    # Build query with explicit joins to handle multiple foreign keys
    query = Cheque.query.join(Client).join(Branch, Cheque.branch_id == Branch.id).join(Bank)
    
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
                         date_to=date_to,
                         date=date)

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
            
            # OPTIMIZATION: Auto-create all monthly sheets for the year when adding a cheque
            excel_folder = Path(current_app.config.get('EXCEL_FOLDER', 'data/excel'))
            auto_creator = AutoSheetCreator(excel_folder)
            sheet_optimization_success, sheet_filepath = auto_creator.optimize_cheque_addition(cheque)
            
            # Automatically update Excel file with optimized sync
            optimized_sync = OptimizedExcelSync(excel_folder)
            excel_sync_success = optimized_sync.sync_cheque(cheque, 'create')
            
            if excel_sync_success:
                if sheet_optimization_success:
                    flash('Chèque ajouté avec succès! Tous les onglets mensuels ont été créés et le fichier Excel synchronisé.', 'success')
                else:
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
            # Update cheque fields (excluding cheque_number - it stays the same)
            cheque.amount = form.amount.data
            cheque.currency = form.currency.data
            cheque.issue_date = form.issue_date.data
            cheque.due_date = form.due_date.data
            cheque.client_id = form.client_id.data
            cheque.branch_id = form.branch_id.data
            cheque.deposit_branch_id = form.deposit_branch_id.data if form.deposit_branch_id.data and form.deposit_branch_id.data != 0 else None
            cheque.status = form.status.data
            # Note: cheque_number is not updated - it remains the original value
            cheque.invoice_number = form.invoice_number.data
            cheque.invoice_date = form.invoice_date.data
            cheque.depositor_name = form.depositor_name.data
            cheque.notes = form.notes.data
            cheque.payment_type = form.payment_type.data
            cheque.created_date = form.created_date.data
            cheque.unpaid_reason = form.unpaid_reason.data if form.status.data == 'IMPAYE' else None
            cheque.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Automatically update Excel file with optimized sync
            excel_folder = Path(current_app.config.get('EXCEL_FOLDER', 'data/excel'))
            optimized_sync = OptimizedExcelSync(excel_folder)
            excel_sync_success = optimized_sync.sync_cheque(cheque, 'update')
            
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
        
        # Remove from Excel before deleting from database with optimized sync
        excel_folder = Path(current_app.config.get('EXCEL_FOLDER', 'data/excel'))
        optimized_sync = OptimizedExcelSync(excel_folder)
        optimized_sync.sync_cheque(cheque, 'delete')
        
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
            'ANNULE': 'ANNULÉ'
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

        # Excel synchronization with proper error handling
        try:
            excel_folder = Path(current_app.config.get('EXCEL_FOLDER', 'data/excel'))
            optimized_sync = OptimizedExcelSync(excel_folder)
            sync_result = optimized_sync.sync_cheque(cheque, 'update')
            
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