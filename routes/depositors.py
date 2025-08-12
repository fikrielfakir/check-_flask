"""
Depositor management routes
Handles CRUD operations for depositors (people who deposit cheques)
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, func
from datetime import datetime, date
import logging
from models import Depositor, DepositLog, User, Cheque, db
from forms import DepositorForm
from utils.decorators import role_required

depositors_bp = Blueprint('depositors', __name__)

@depositors_bp.route('/depositors')
@login_required
@role_required(['admin', 'comptable', 'agent'])
def list_depositors():
    """List all depositors with search and filtering"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    depositor_type = request.args.get('type', '')
    status = request.args.get('status', '')
    risk_level = request.args.get('risk', '')
    
    # Build query
    query = Depositor.query
    
    # Apply search filter
    if search:
        search_filter = or_(
            Depositor.name.contains(search),
            Depositor.phone.contains(search),
            Depositor.email.contains(search),
            Depositor.id_number.contains(search),
            Depositor.company_name.contains(search)
        )
        query = query.filter(search_filter)
    
    # Apply type filter
    if depositor_type:
        query = query.filter(Depositor.type == depositor_type)
    
    # Apply status filter
    if status == 'active':
        query = query.filter(Depositor.is_active == True)
    elif status == 'inactive':
        query = query.filter(Depositor.is_active == False)
    elif status == 'blocked':
        query = query.filter(Depositor.blocked == True)
    
    # Apply risk level filter
    if risk_level:
        query = query.filter(Depositor.risk_level == risk_level)
    
    # Order by most recent activity
    query = query.order_by(Depositor.last_deposit_date.desc().nullslast(), 
                          Depositor.created_at.desc())
    
    # Paginate results
    depositors = query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get summary statistics
    total_depositors = Depositor.query.count()
    active_depositors = Depositor.query.filter(Depositor.is_active == True).count()
    blocked_depositors = Depositor.query.filter(Depositor.blocked == True).count()
    high_risk_depositors = Depositor.query.filter(Depositor.risk_level == 'high').count()
    
    stats = {
        'total': total_depositors,
        'active': active_depositors,
        'blocked': blocked_depositors,
        'high_risk': high_risk_depositors,
        'inactive': total_depositors - active_depositors
    }
    
    return render_template('depositors/list.html',
                         depositors=depositors,
                         search=search,
                         depositor_type=depositor_type,
                         status=status,
                         risk_level=risk_level,
                         stats=stats)

@depositors_bp.route('/depositors/new', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'comptable', 'agent'])
def create_depositor():
    """Create a new depositor"""
    form = DepositorForm()
    
    if form.validate_on_submit():
        try:
            depositor = Depositor(
                name=form.name.data,
                type=form.type.data,
                phone=form.phone.data,
                email=form.email.data,
                address=form.address.data,
                city=form.city.data,
                postal_code=form.postal_code.data,
                id_number=form.id_number.data,
                id_type=form.id_type.data,
                company_name=form.company_name.data,
                job_title=form.job_title.data,
                bank_account_number=form.bank_account_number.data,
                bank_name=form.bank_name.data,
                bank_branch=form.bank_branch.data,
                notes=form.notes.data,
                created_by=current_user.id
            )
            
            db.session.add(depositor)
            db.session.commit()
            
            flash(f'Déposant {depositor.name} créé avec succès.', 'success')
            logging.info(f"Depositor created: {depositor.name} by user {current_user.username}")
            
            return redirect(url_for('depositors.list_depositors'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du déposant: {str(e)}', 'error')
            logging.error(f"Error creating depositor: {str(e)}")
    
    return render_template('depositors/form.html', form=form, title='Nouveau Déposant')

@depositors_bp.route('/depositors/<int:id>')
@login_required
@role_required(['admin', 'comptable', 'agent', 'user'])
def view_depositor(id):
    """View depositor details"""
    depositor = Depositor.query.get_or_404(id)
    
    # Get recent deposits
    recent_deposits = DepositLog.query.filter_by(depositor_id=id)\
        .order_by(DepositLog.deposit_date.desc())\
        .limit(10).all()
    
    # Get associated cheques
    recent_cheques = Cheque.query.filter_by(depositor_id=id)\
        .order_by(Cheque.created_date.desc())\
        .limit(10).all()
    
    # Calculate deposit statistics
    deposit_stats = db.session.query(
        func.count(DepositLog.id).label('total_deposits'),
        func.sum(Cheque.amount).label('total_amount'),
        func.count(db.case([(DepositLog.status == 'completed', 1)])).label('successful_deposits'),
        func.count(db.case([(DepositLog.status == 'rejected', 1)])).label('rejected_deposits')
    ).join(Cheque, DepositLog.cheque_id == Cheque.id)\
     .filter(DepositLog.depositor_id == id).first()
    
    return render_template('depositors/detail.html',
                         depositor=depositor,
                         recent_deposits=recent_deposits,
                         recent_cheques=recent_cheques,
                         deposit_stats=deposit_stats)

@depositors_bp.route('/depositors/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'comptable', 'agent'])
def edit_depositor(id):
    """Edit depositor information"""
    depositor = Depositor.query.get_or_404(id)
    form = DepositorForm(obj=depositor)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(depositor)
            depositor.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash(f'Déposant {depositor.name} modifié avec succès.', 'success')
            logging.info(f"Depositor updated: {depositor.name} by user {current_user.username}")
            
            return redirect(url_for('depositors.view_depositor', id=depositor.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification du déposant: {str(e)}', 'error')
            logging.error(f"Error updating depositor: {str(e)}")
    
    return render_template('depositors/form.html',
                         form=form,
                         depositor=depositor,
                         title=f'Modifier - {depositor.name}')

@depositors_bp.route('/depositors/<int:id>/toggle-status', methods=['POST'])
@login_required
@role_required(['admin', 'comptable'])
def toggle_depositor_status(id):
    """Toggle depositor active/inactive status"""
    depositor = Depositor.query.get_or_404(id)
    
    try:
        depositor.is_active = not depositor.is_active
        depositor.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        status = "activé" if depositor.is_active else "désactivé"
        flash(f'Déposant {depositor.name} {status} avec succès.', 'success')
        logging.info(f"Depositor status changed: {depositor.name} -> {status} by {current_user.username}")
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors du changement de statut: {str(e)}', 'error')
        logging.error(f"Error toggling depositor status: {str(e)}")
    
    return redirect(url_for('depositors.view_depositor', id=id))

@depositors_bp.route('/depositors/<int:id>/block', methods=['POST'])
@login_required
@role_required(['admin', 'comptable'])
def block_depositor(id):
    """Block/unblock a depositor"""
    depositor = Depositor.query.get_or_404(id)
    
    try:
        depositor.blocked = not depositor.blocked
        
        if depositor.blocked:
            depositor.blocked_date = date.today()
            depositor.blocked_by = current_user.id
            depositor.blocked_reason = request.form.get('reason', 'Bloqué par l\'administrateur')
            action = "bloqué"
        else:
            depositor.blocked_date = None
            depositor.blocked_by = None
            depositor.blocked_reason = None
            action = "débloqué"
        
        depositor.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash(f'Déposant {depositor.name} {action} avec succès.', 'success')
        logging.info(f"Depositor {action}: {depositor.name} by {current_user.username}")
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors du blocage/déblocage: {str(e)}', 'error')
        logging.error(f"Error blocking/unblocking depositor: {str(e)}")
    
    return redirect(url_for('depositors.view_depositor', id=id))

@depositors_bp.route('/api/depositors/search')
@login_required
def search_depositors():
    """API endpoint for depositor search (for AJAX autocomplete)"""
    query = request.args.get('q', '')
    active_only = request.args.get('active_only', '1') == '1'
    limit = min(request.args.get('limit', 10, type=int), 50)
    
    if not query or len(query) < 2:
        return jsonify([])
    
    # Build search query
    search_filter = or_(
        Depositor.name.contains(query),
        Depositor.phone.contains(query),
        Depositor.id_number.contains(query),
        Depositor.company_name.contains(query)
    )
    
    depositors_query = Depositor.query.filter(search_filter)
    
    if active_only:
        depositors_query = depositors_query.filter(
            Depositor.is_active == True,
            Depositor.blocked == False
        )
    
    depositors = depositors_query.limit(limit).all()
    
    results = []
    for depositor in depositors:
        results.append({
            'id': depositor.id,
            'name': depositor.name,
            'type': depositor.type,
            'phone': depositor.phone,
            'company_name': depositor.company_name,
            'is_active': depositor.is_active,
            'blocked': depositor.blocked,
            'total_deposits': depositor.total_deposits,
            'text': f"{depositor.name}" + (f" ({depositor.company_name})" if depositor.company_name else ""),
            'risk_level': depositor.risk_level
        })
    
    return jsonify(results)

@depositors_bp.route('/depositors/stats')
@login_required
@role_required(['admin', 'comptable', 'agent'])
def depositor_stats():
    """Get depositor statistics for dashboard"""
    
    # Monthly deposit trends
    monthly_stats = db.session.query(
        func.strftime('%Y-%m', DepositLog.deposit_date).label('month'),
        func.count(DepositLog.id).label('deposits'),
        func.sum(Cheque.amount).label('total_amount'),
        func.count(func.distinct(DepositLog.depositor_id)).label('unique_depositors')
    ).join(Cheque, DepositLog.cheque_id == Cheque.id)\
     .group_by(func.strftime('%Y-%m', DepositLog.deposit_date))\
     .order_by(func.strftime('%Y-%m', DepositLog.deposit_date).desc())\
     .limit(12).all()
    
    # Top depositors
    top_depositors = db.session.query(
        Depositor.name,
        Depositor.type,
        func.count(DepositLog.id).label('deposits'),
        func.sum(Cheque.amount).label('total_amount')
    ).join(DepositLog, Depositor.id == DepositLog.depositor_id)\
     .join(Cheque, DepositLog.cheque_id == Cheque.id)\
     .group_by(Depositor.id, Depositor.name, Depositor.type)\
     .order_by(func.count(DepositLog.id).desc())\
     .limit(10).all()
    
    # Risk level distribution
    risk_distribution = db.session.query(
        Depositor.risk_level,
        func.count(Depositor.id).label('count')
    ).group_by(Depositor.risk_level).all()
    
    return jsonify({
        'monthly_trends': [
            {
                'month': stat.month,
                'deposits': stat.deposits,
                'total_amount': float(stat.total_amount or 0),
                'unique_depositors': stat.unique_depositors
            } for stat in monthly_stats
        ],
        'top_depositors': [
            {
                'name': depositor.name,
                'type': depositor.type,
                'deposits': depositor.deposits,
                'total_amount': float(depositor.total_amount or 0)
            } for depositor in top_depositors
        ],
        'risk_distribution': [
            {
                'level': risk.risk_level,
                'count': risk.count
            } for risk in risk_distribution
        ]
    })

@depositors_bp.route('/api/create', methods=['POST'])
@login_required
@role_required(['admin', 'comptable', 'agent'])
def api_create():
    """API endpoint for creating new depositors via AJAX"""
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({'error': 'Le nom du déposant est requis'}), 400
        
        # Create new depositor
        depositor = Depositor(
            name=data['name'].strip(),
            type=data.get('type', 'personne'),
            phone=data.get('phone', '').strip() or None,
            email=data.get('email', '').strip() or None,
            address=data.get('address', '').strip() or None,
            city=data.get('city', '').strip() or None,
            postal_code=data.get('postal_code', '').strip() or None,
            id_number=data.get('id_number', '').strip() or None,
            id_type=data.get('id_type', '').strip() or None,
            company_name=data.get('company_name', '').strip() or None,
            job_title=data.get('job_title', '').strip() or None,
            bank_account_number=data.get('bank_account_number', '').strip() or None,
            bank_name=data.get('bank_name', '').strip() or None,
            bank_branch=data.get('bank_branch', '').strip() or None,
            notes=data.get('notes', '').strip() or None,
            is_active=True,
            created_by=current_user.id
        )
        
        # Check for duplicate
        existing = Depositor.query.filter(
            Depositor.name == depositor.name
        ).first()
        
        if existing:
            return jsonify({'error': 'Un déposant avec ce nom existe déjà'}), 400
        
        db.session.add(depositor)
        db.session.commit()
        
        # Return created depositor data
        display_name = depositor.name
        if depositor.company_name:
            display_name += f" ({depositor.company_name})"
        
        return jsonify({
            'id': depositor.id,
            'name': depositor.name,
            'type': depositor.type,
            'display_name': display_name,
            'company_name': depositor.company_name,
            'phone': depositor.phone
        })
        
    except Exception as e:
        logging.error(f"Error creating depositor via API: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erreur lors de la création du déposant'}), 500