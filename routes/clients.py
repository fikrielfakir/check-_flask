from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Client
from forms import ClientForm
from app import db
from sqlalchemy import or_, func, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import re
import logging
import csv
from io import StringIO
from datetime import datetime
from functools import wraps
import time
from models import Client, Cheque  # Make sure Cheque is imported

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

clients_bp = Blueprint('clients', __name__)

# Constants
MOROCCAN_ID_PATTERNS = {
    'cin': r'^[A-Z]{1,2}\d{3,6}$',
    'if': r'^\d{9}$',
    'rc': r'^\d+$',
    'ice': r'^\d{15}$'
}

CLIENT_TYPES = {
    'personne': {
        'display': 'Personne physique',
        'id_field': 'CIN',
        'vat_field': 'IF'
    },
    'entreprise': {
        'display': 'Entreprise',
        'id_field': 'RC',
        'vat_field': 'ICE'
    }
}

# Performance monitoring decorator
def monitor_performance(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            execution_time = time.time() - start_time
            if execution_time > 1.0:  # Log slow queries
                logger.warning(f"Slow operation in {f.__name__}: {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error in {f.__name__} after {execution_time:.2f}s: {e}")
            raise
    return decorated_function

# Access control decorator
def require_role(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Vous devez être connecté.', 'warning')
                return redirect(url_for('auth.login'))
            
            if current_user.role not in roles:
                flash('Accès refusé. Permissions insuffisantes.', 'danger')
                return redirect(url_for('clients.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def check_access():
    """Check if current user has access to manage clients"""
    if not current_user.is_authenticated:
        return False
    return current_user.role in ['admin', 'comptable', 'agent']

class ClientValidator:
    """Centralized client validation logic"""
    
    @staticmethod
    def validate_moroccan_ids(client_type, id_number, vat_number):
        """Validate Moroccan identification numbers with enhanced checks"""
        errors = []
        
        if not client_type or client_type not in CLIENT_TYPES:
            errors.append('Type de client invalide')
            return errors
        
        if client_type == 'personne':
            if id_number:
                id_number = id_number.strip().upper()

                # CIN: 1 ou 2 lettres + 3 à 6 chiffres (ex: RX3653, K1234, AB123456)
                if not re.match(MOROCCAN_ID_PATTERNS['cin'], id_number):
                    errors.append('Le CIN doit contenir 1 ou 2 lettres suivies de 3 à 6 chiffres (ex: RX3653, K1234, AB123456)')
   

            
            if vat_number:
                vat_number = vat_number.strip()
                if not re.match(MOROCCAN_ID_PATTERNS['if'], vat_number):
                    errors.append('L\'IF doit contenir exactement 9 chiffres')
        
        elif client_type == 'entreprise':
            if id_number:
                id_number = id_number.strip()
                if not re.match(MOROCCAN_ID_PATTERNS['rc'], id_number):
                    errors.append('Le RC doit contenir uniquement des chiffres')
            
            if vat_number:
                vat_number = vat_number.strip()
                if not re.match(MOROCCAN_ID_PATTERNS['ice'], vat_number):
                    errors.append('L\'ICE doit contenir exactement 15 chiffres')
                elif not ClientValidator._validate_ice_checksum(vat_number):
                    errors.append('L\'ICE fourni n\'est pas valide (erreur de contrôle)')
        
        return errors
    
    @staticmethod
    def _validate_cin_checksum(cin):
        """Validate CIN checksum (simplified validation)"""
        try:
            # Basic validation - you can implement more sophisticated checksum if needed
            letters = cin[:2]
            numbers = cin[2:]
            return len(letters) == 2 and len(numbers) == 6 and numbers.isdigit()
        except:
            return False
    
    @staticmethod
    def _validate_ice_checksum(ice):
        """Validate ICE checksum using Luhn algorithm"""
        try:
            # Implement Luhn algorithm for ICE validation
            def luhn_checksum(card_num):
                def digits_of(n):
                    return [int(d) for d in str(n)]
                digits = digits_of(card_num)
                odd_digits = digits[-1::-2]
                even_digits = digits[-2::-2]
                checksum = sum(odd_digits)
                for d in even_digits:
                    checksum += sum(digits_of(d*2))
                return checksum % 10
            
            return luhn_checksum(ice) == 0
        except:
            return False
    
    @staticmethod
    def sanitize_client_data(data):
        """Sanitize and normalize client data"""
        sanitized = {}
        
        if 'name' in data:
            sanitized['name'] = data['name'].strip().title() if data['name'] else None
        
        if 'type' in data:
            sanitized['type'] = data['type'].lower() if data['type'] in CLIENT_TYPES else None
        
        if 'id_number' in data and data['id_number']:
            id_num = data['id_number'].strip()
            sanitized['id_number'] = id_num.upper() if data.get('type') == 'personne' else id_num
        else:
            sanitized['id_number'] = None
        
        if 'vat_number' in data and data['vat_number']:
            sanitized['vat_number'] = data['vat_number'].strip()
        else:
            sanitized['vat_number'] = None
        
        return sanitized

class ClientService:
    """Service layer for client operations"""
    
    @staticmethod
    @monitor_performance
    def check_duplicate_client(name, client_type, id_number=None, vat_number=None, exclude_id=None):
        """Check for duplicate clients with optimized queries"""
        try:
            if not name or not client_type:
                return None
            
            # Use efficient exists() queries instead of full object retrieval
            base_query = db.session.query(Client.id)
            
            if exclude_id:
                base_query = base_query.filter(Client.id != exclude_id)
            
            # Check for duplicate name (case insensitive, trimmed)
            name_exists = base_query.filter(
                func.lower(func.trim(Client.name)) == func.lower(name.strip())
            ).first()
            
            if name_exists:
                return f"Un client avec le nom '{name}' existe déjà"
            
            # Check for duplicate ID numbers
            if id_number and id_number.strip():
                id_clean = id_number.strip().upper() if client_type == 'personne' else id_number.strip()
                id_exists = base_query.filter(
                    func.upper(func.trim(Client.id_number)) == func.upper(id_clean)
                ).first()
                
                if id_exists:
                    id_type = CLIENT_TYPES[client_type]['id_field']
                    return f"Un client avec ce {id_type} ({id_number}) existe déjà"
            
            # Check for duplicate VAT numbers
            if vat_number and vat_number.strip():
                vat_exists = base_query.filter(
                    func.trim(Client.vat_number) == vat_number.strip()
                ).first()
                
                if vat_exists:
                    vat_type = CLIENT_TYPES[client_type]['vat_field']
                    return f"Un client avec cet {vat_type} ({vat_number}) existe déjà"
            
            return None
            
        except SQLAlchemyError as e:
            logger.error(f"Database error checking duplicate client: {e}")
            return "Erreur lors de la vérification des doublons"
        except Exception as e:
            logger.error(f"Unexpected error checking duplicate client: {e}")
            return "Erreur inattendue lors de la vérification"
            return False, "Erreur lors de la vérification des associations", {}

    @staticmethod
    @monitor_performance
    def create_client(data):
        """Create a new client with full validation"""
        try:
            # Sanitize data
            clean_data = ClientValidator.sanitize_client_data(data)
            
            # Validate
            validation_errors = ClientValidator.validate_moroccan_ids(
                clean_data['type'], clean_data['id_number'], clean_data['vat_number']
            )
            
            if validation_errors:
                return False, validation_errors[0], None
            
            # Check duplicates
            duplicate_error = ClientService.check_duplicate_client(
                clean_data['name'], clean_data['type'],
                clean_data['id_number'], clean_data['vat_number']
            )
            
            if duplicate_error:
                return False, duplicate_error, None
            
            # Create client
            client = Client(
                type=clean_data['type'],
                name=clean_data['name'],
                id_number=clean_data['id_number'],
                vat_number=clean_data['vat_number']
            )
            
            db.session.add(client)
            db.session.flush()  # Get the ID without committing
            db.session.commit()
            
            logger.info(f"New client created: {client.name} (ID: {client.id}) by user {current_user.username}")
            return True, "Client créé avec succès", client
            
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"Integrity error creating client: {e}")
            return False, "Erreur d'intégrité des données", None
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error creating client: {e}")
            return False, "Erreur de base de données", None
        except Exception as e:
            db.session.rollback()
            logger.error(f"Unexpected error creating client: {e}")
            return False, "Erreur inattendue lors de la création", None

# Routes
@clients_bp.route('/')
@login_required
@monitor_performance
def index():
    try:
        # Get parameters with defaults
        search = request.args.get('search', '').strip()
        client_type = request.args.get('type', '')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Limit max per_page
        sort_by = request.args.get('sort', 'name')
        sort_order = request.args.get('order', 'asc')
        
        # Build optimized query
        query = Client.query
        
        # Search filter with index-friendly operations
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                or_(
                    Client.name.ilike(search_term),
                    Client.id_number.ilike(search_term),
                    Client.vat_number.ilike(search_term)
                )
            )
        
        # Type filter
        if client_type and client_type in CLIENT_TYPES:
            query = query.filter(Client.type == client_type)
        
        # Sorting
        sort_column = getattr(Client, sort_by, Client.name)
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Pagination with error handling
        try:
            clients = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
        except Exception as e:
            logger.warning(f"Pagination error: {e}")
            clients = query.paginate(page=1, per_page=per_page, error_out=False)
        
        # Get statistics for dashboard
        stats = {
            'total': Client.query.count(),
            'personnes': Client.query.filter_by(type='personne').count(),
            'entreprises': Client.query.filter_by(type='entreprise').count()
        }
        
        return render_template('clients/index.html', 
                             clients=clients, 
                             search=search, 
                             client_type=client_type,
                             sort_by=sort_by,
                             sort_order=sort_order,
                             stats=stats,
                             client_types=CLIENT_TYPES)
                             
    except Exception as e:
        logger.error(f"Error in clients index: {e}")
        flash('Erreur lors du chargement des clients.', 'danger')
        return render_template('clients/index.html', 
                             clients=None, 
                             search='', 
                             client_type='',
                             stats={},
                             client_types=CLIENT_TYPES)

@clients_bp.route('/new', methods=['GET', 'POST'])
@login_required
@require_role('admin', 'comptable', 'agent')
@monitor_performance
def new():
    form = ClientForm()
    
    if form.validate_on_submit():
        success, message, client = ClientService.create_client({
            'type': form.type.data,
            'name': form.name.data,
            'id_number': form.id_number.data,
            'vat_number': form.vat_number.data
        })
        
        if success:
            flash(message, 'success')
            return redirect(url_for('clients.index'))
        else:
            flash(message, 'danger')
    
    return render_template('clients/form.html', 
                         form=form, 
                         title='Nouveau Client',
                         client_types=CLIENT_TYPES)

@clients_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@require_role('admin', 'comptable', 'agent')
@monitor_performance
def edit(id):
    try:
        client = Client.query.get_or_404(id)
        form = ClientForm(obj=client)
        
        if form.validate_on_submit():
            # Sanitize data
            clean_data = ClientValidator.sanitize_client_data({
                'type': form.type.data,
                'name': form.name.data,
                'id_number': form.id_number.data,
                'vat_number': form.vat_number.data
            })
            
            # Validate
            validation_errors = ClientValidator.validate_moroccan_ids(
                clean_data['type'], clean_data['id_number'], clean_data['vat_number']
            )
            
            if validation_errors:
                flash(validation_errors[0], 'danger')
                return render_template('clients/form.html', 
                                     form=form, 
                                     title='Modifier Client', 
                                     client=client,
                                     client_types=CLIENT_TYPES)
            
            # Check for duplicates (excluding current client)
            duplicate_error = ClientService.check_duplicate_client(
                clean_data['name'], clean_data['type'],
                clean_data['id_number'], clean_data['vat_number'],
                exclude_id=id
            )
            
            if duplicate_error:
                flash(duplicate_error, 'danger')
                return render_template('clients/form.html', 
                                     form=form, 
                                     title='Modifier Client', 
                                     client=client,
                                     client_types=CLIENT_TYPES)
            
            # Update client
            old_name = client.name
            client.type = clean_data['type']
            client.name = clean_data['name']
            client.id_number = clean_data['id_number']
            client.vat_number = clean_data['vat_number']
            client.updated_at = datetime.utcnow()  # Add if you have this field
            
            db.session.commit()
            
            logger.info(f"Client updated: {old_name} -> {client.name} (ID: {client.id}) by user {current_user.username}")
            flash('Client modifié avec succès!', 'success')
            return redirect(url_for('clients.index'))
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating client {id}: {e}")
        flash('Erreur lors de la modification du client.', 'danger')
        return redirect(url_for('clients.index'))
    
    return render_template('clients/form.html', 
                         form=form, 
                         title='Modifier Client', 
                         client=client,
                         client_types=CLIENT_TYPES)
@clients_bp.route('/<int:id>/view')
@login_required
@monitor_performance
def view(id):
    """View client details with related data"""
    try:
        client = Client.query.get_or_404(id)
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # Get client's cheques with optimized query
        cheques = None
        try:
            # Correct way to query related cheques with ordering
            cheques = Cheque.query.filter_by(client_id=client.id)\
                                 .order_by(Cheque.created_at.desc())\
                                 .paginate(page=page, per_page=per_page, error_out=False)
        except Exception as e:
            logger.warning(f"Error loading cheques for client {id}: {e}")
            flash("Erreur lors du chargement des chèques associés", "warning")
        
        # Get relationship summary
        can_delete, reason, related_counts = ClientService.safe_check_client_relationships(client)
        
        return render_template('clients/view.html', 
                            client=client, 
                            cheques=cheques,
                            can_delete=can_delete,
                            related_counts=related_counts,
                            client_types=CLIENT_TYPES)
        
    except Exception as e:
        logger.error(f"Error viewing client {id}: {e}")
        flash('Erreur lors du chargement du client.', 'danger')
        return redirect(url_for('clients.index'))

@clients_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@require_role('admin')
@monitor_performance
def delete(id):
    try:
        client = Client.query.get_or_404(id)
        
        # Comprehensive relationship check
        can_delete, reason, related_counts = ClientService.safe_check_client_relationships(client)
        
        if not can_delete:
            flash(f'Impossible de supprimer ce client: {reason}', 'danger')
            return redirect(url_for('clients.view', id=id))
        
        # Store info for logging
        client_name = client.name
        client_id = client.id
        
        try:
            # Perform deletion with transaction
            db.session.delete(client)
            db.session.flush()  # Check for constraint violations
            db.session.commit()
            
            logger.info(f"Client deleted: {client_name} (ID: {client_id}) by user {current_user.username}")
            flash('Client supprimé avec succès!', 'success')
            
        except IntegrityError as ie:
            db.session.rollback()
            error_msg = str(ie.orig).lower()
            
            if 'foreign key' in error_msg or 'constraint' in error_msg:
                if 'cheque' in error_msg:
                    flash('Impossible de supprimer ce client car il a des chèques associés.', 'danger')
                else:
                    flash('Impossible de supprimer ce client car il est référencé par d\'autres données.', 'danger')
            else:
                logger.error(f"Integrity error deleting client {id}: {ie}")
                flash('Erreur d\'intégrité des données lors de la suppression.', 'danger')
            
            return redirect(url_for('clients.view', id=id))
        
        except SQLAlchemyError as se:
            db.session.rollback()
            logger.error(f"Database error deleting client {id}: {se}")
            flash('Erreur de base de données lors de la suppression.', 'danger')
            return redirect(url_for('clients.view', id=id))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error deleting client {id}: {e}")
        
        if "404" in str(e) or "not found" in str(e).lower():
            flash('Client introuvable.', 'danger')
        else:
            flash('Erreur inattendue lors de la suppression du client.', 'danger')
    
    return redirect(url_for('clients.index'))

@clients_bp.route('/api/search')
@login_required
@monitor_performance
def api_search():
    """Optimized API endpoint for client autocomplete"""
    try:
        query_param = request.args.get('q', '').strip()
        limit = min(request.args.get('limit', 10, type=int), 50)  # Limit results
        
        if len(query_param) < 2:
            return jsonify([])
        
        search_term = f'%{query_param}%'
        
        # Optimized query with specific columns
        clients = db.session.query(
            Client.id,
            Client.name,
            Client.type,
            Client.id_number,
            Client.vat_number
        ).filter(
            or_(
                Client.name.ilike(search_term),
                Client.id_number.ilike(search_term),
                Client.vat_number.ilike(search_term)
            )
        ).order_by(Client.name).limit(limit).all()
        
        results = []
        for client in clients:
            id_info = client.id_number or client.vat_number or 'Sans ID'
            type_display = CLIENT_TYPES.get(client.type, {}).get('display', client.type)
            
            results.append({
                'id': client.id,
                'name': client.name,
                'type': client.type,
                'type_display': type_display,
                'id_number': client.id_number,
                'vat_number': client.vat_number,
                'display_text': f"{client.name} ({id_info})",
                'subtitle': type_display
            })
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in client search API: {e}")
        return jsonify({'error': 'Erreur lors de la recherche'}), 500

@clients_bp.route('/api/create', methods=['POST'])
@login_required
@require_role('admin', 'comptable', 'agent')
@monitor_performance
def api_create():
    """API endpoint to create a new client"""
    try:
        data = request.get_json()
        
        if not data or not data.get('name') or not data.get('type'):
            return jsonify({'error': 'Nom et type sont requis'}), 400
        
        success, message, client = ClientService.create_client(data)
        
        if success:
            return jsonify({
                'id': client.id,
                'name': client.name,
                'type': client.type,
                'type_display': CLIENT_TYPES.get(client.type, {}).get('display', client.type),
                'id_number': client.id_number,
                'vat_number': client.vat_number,
                'message': message
            })
        else:
            return jsonify({'error': message}), 400
        
    except Exception as e:
        logger.error(f"Error creating client via API: {e}")
        return jsonify({'error': 'Erreur lors de la création du client'}), 500

@clients_bp.route('/api/validate', methods=['POST'])
@login_required
@monitor_performance
def api_validate():
    """API endpoint for real-time validation"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'valid': False, 'errors': ['Données manquantes']})
        
        errors = []
        
        # Sanitize data first
        clean_data = ClientValidator.sanitize_client_data(data)
        
        # Validate identification numbers
        if clean_data.get('type'):
            id_errors = ClientValidator.validate_moroccan_ids(
                clean_data['type'], clean_data.get('id_number'), clean_data.get('vat_number')
            )
            errors.extend(id_errors)
        
        # Check for duplicates if validation passes
        if not errors and clean_data.get('name') and clean_data.get('type'):
            duplicate_error = ClientService.check_duplicate_client(
                clean_data['name'], clean_data['type'],
                clean_data.get('id_number'), clean_data.get('vat_number'),
                exclude_id=data.get('exclude_id')
            )
            if duplicate_error:
                errors.append(duplicate_error)
        
        return jsonify({
            'valid': len(errors) == 0,
            'errors': errors,
            'sanitized_data': clean_data
        })
        
    except Exception as e:
        logger.error(f"Error in validation API: {e}")
        return jsonify({
            'valid': False,
            'errors': ['Erreur lors de la validation']
        }), 500

@clients_bp.route('/export')
@login_required
@require_role('admin', 'comptable')
@monitor_performance
def export():
    """Export clients to CSV with optimized query"""
    try:
        # Get filters from query params
        search = request.args.get('search', '').strip()
        client_type = request.args.get('type', '')
        
        # Build query
        query = db.session.query(
            Client.type,
            Client.name,
            Client.id_number,
            Client.vat_number,
            Client.created_at
        )
        
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                or_(
                    Client.name.ilike(search_term),
                    Client.id_number.ilike(search_term),
                    Client.vat_number.ilike(search_term)
                )
            )
        
        if client_type and client_type in CLIENT_TYPES:
            query = query.filter(Client.type == client_type)
        
        clients = query.order_by(Client.name).all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Type', 'Nom', 'CIN/RC', 'IF/ICE', 'Date de création'
        ])
        
        # Write data
        for client in clients:
            writer.writerow([
                CLIENT_TYPES.get(client.type, {}).get('display', client.type),
                client.name,
                client.id_number or '',
                client.vat_number or '',
                client.created_at.strftime('%d/%m/%Y %H:%M') if client.created_at else ''
            ])
        
        output.seek(0)
        
        # Create response
        from flask import make_response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=clients_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        logger.info(f"Clients exported by user {current_user.username} ({len(clients)} records)")
        return response
        
    except Exception as e:
        logger.error(f"Error exporting clients: {e}")
        flash('Erreur lors de l\'export des clients.', 'danger')
        return redirect(url_for('clients.index'))

@clients_bp.route('/stats')
@login_required
@monitor_performance
def stats():
    """Comprehensive client statistics with caching"""
    try:
        # Basic stats
        total_clients = Client.query.count()
        personnes_count = Client.query.filter_by(type='personne').count()
        entreprises_count = Client.query.filter_by(type='entreprise').count()
        
        # Advanced stats
        with_id_number = Client.query.filter(Client.id_number.isnot(None)).count()
        with_vat_number = Client.query.filter(Client.vat_number.isnot(None)).count()
        
        # Recent activity (if you have created_at field)
        try:
            from datetime import datetime, timedelta
            last_30_days = datetime.utcnow() - timedelta(days=30)
            recent_clients = Client.query.filter(
                Client.created_at >= last_30_days
            ).count() if hasattr(Client, 'created_at') else 0
        except:
            recent_clients = 0
        
        # Monthly stats (if you have created_at field)
        monthly_stats = []
        if hasattr(Client, 'created_at'):
            try:
                from sqlalchemy import extract
                for i in range(6):  # Last 6 months
                    month_date = datetime.utcnow() - timedelta(days=30*i)
                    count = Client.query.filter(
                        extract('year', Client.created_at) == month_date.year,
                        extract('month', Client.created_at) == month_date.month
                    ).count()
                    monthly_stats.append({
                        'month': month_date.strftime('%Y-%m'),
                        'month_name': month_date.strftime('%B %Y'),
                        'count': count
                    })
                monthly_stats.reverse()
            except:
                monthly_stats = []
        
        stats_data = {
            'total_clients': total_clients,
            'personnes': personnes_count,
            'entreprises': entreprises_count,
            'with_id_number': with_id_number,
            'with_vat_number': with_vat_number,
            'recent_clients': recent_clients,
            'monthly_stats': monthly_stats,
            'completion_rate': {
                'id_numbers': round((with_id_number / total_clients * 100) if total_clients > 0 else 0, 1),
                'vat_numbers': round((with_vat_number / total_clients * 100) if total_clients > 0 else 0, 1)
            }
        }
        
        return jsonify(stats_data)
        
    except Exception as e:
        logger.error(f"Error getting client stats: {e}")
        return jsonify({'error': 'Erreur lors du chargement des statistiques'}), 500

@clients_bp.route('/bulk-import', methods=['GET', 'POST'])
@login_required
@require_role('admin', 'comptable')
@monitor_performance
def bulk_import():
    """Bulk import clients from CSV"""
    if request.method == 'GET':
        return render_template('clients/bulk_import.html')
    
    try:
        if 'file' not in request.files:
            flash('Aucun fichier sélectionné.', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('Aucun fichier sélectionné.', 'danger')
            return redirect(request.url)
        
        if not file.filename.lower().endswith('.csv'):
            flash('Seuls les fichiers CSV sont acceptés.', 'danger')
            return redirect(request.url)
        
        # Read and parse CSV
        try:
            content = file.read().decode('utf-8')
            csv_reader = csv.DictReader(StringIO(content))
        except UnicodeDecodeError:
            try:
                file.seek(0)
                content = file.read().decode('iso-8859-1')
                csv_reader = csv.DictReader(StringIO(content))
            except:
                flash('Erreur d\'encodage du fichier. Utilisez UTF-8 ou ISO-8859-1.', 'danger')
                return redirect(request.url)
        
        # Import statistics
        import_stats = {
            'total': 0,
            'success': 0,
            'errors': 0,
            'skipped': 0,
            'error_details': []
        }
        
        # Process each row
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for header
            import_stats['total'] += 1
            
            try:
                # Expected columns: Type, Nom, CIN_RC, IF_ICE
                client_type = row.get('Type', '').lower().strip()
                if client_type == 'personne physique':
                    client_type = 'personne'
                elif client_type == 'entreprise':
                    client_type = 'entreprise'
                
                name = row.get('Nom', '').strip()
                id_number = row.get('CIN_RC', '').strip()
                vat_number = row.get('IF_ICE', '').strip()
                
                # Skip empty rows
                if not name or not client_type:
                    import_stats['skipped'] += 1
                    continue
                
                # Validate
                if client_type not in CLIENT_TYPES:
                    import_stats['errors'] += 1
                    import_stats['error_details'].append(f"Ligne {row_num}: Type invalide '{client_type}'")
                    continue
                
                # Check if client already exists
                existing = ClientService.check_duplicate_client(name, client_type, id_number, vat_number)
                if existing:
                    import_stats['skipped'] += 1
                    import_stats['error_details'].append(f"Ligne {row_num}: {existing}")
                    continue
                
                # Create client
                success, message, client = ClientService.create_client({
                    'type': client_type,
                    'name': name,
                    'id_number': id_number if id_number else None,
                    'vat_number': vat_number if vat_number else None
                })
                
                if success:
                    import_stats['success'] += 1
                else:
                    import_stats['errors'] += 1
                    import_stats['error_details'].append(f"Ligne {row_num}: {message}")
                
            except Exception as row_error:
                import_stats['errors'] += 1
                import_stats['error_details'].append(f"Ligne {row_num}: Erreur inattendue - {str(row_error)}")
                logger.error(f"Error processing row {row_num}: {row_error}")
        
        # Generate summary message
        if import_stats['success'] > 0:
            flash(f"Import terminé: {import_stats['success']} clients créés, "
                  f"{import_stats['skipped']} ignorés, {import_stats['errors']} erreurs.", 'info')
        else:
            flash(f"Aucun client importé. {import_stats['errors']} erreurs détectées.", 'warning')
        
        # Log import activity
        logger.info(f"Bulk import by {current_user.username}: {import_stats}")
        
        return render_template('clients/bulk_import.html', import_stats=import_stats)
        
    except Exception as e:
        logger.error(f"Error in bulk import: {e}")
        flash('Erreur lors de l\'import des clients.', 'danger')
        return redirect(request.url)

@clients_bp.route('/merge')
@login_required
@require_role('admin')
def merge_clients():
    """Interface for merging duplicate clients"""
    try:
        # Find potential duplicates based on name similarity
        potential_duplicates = []
        
        # Get all clients ordered by name
        all_clients = Client.query.order_by(Client.name).all()
        
        # Simple duplicate detection based on name similarity
        for i, client1 in enumerate(all_clients):
            for client2 in all_clients[i+1:]:
                # Calculate similarity (simple approach)
                name1 = client1.name.lower().strip()
                name2 = client2.name.lower().strip()
                
                # Check for exact match or very similar names
                if (name1 == name2 or 
                    (len(name1) > 3 and name1 in name2) or 
                    (len(name2) > 3 and name2 in name1)):
                    
                    potential_duplicates.append({
                        'client1': client1,
                        'client2': client2,
                        'similarity': 'high'
                    })
        
        return render_template('clients/merge.html', duplicates=potential_duplicates)
        
    except Exception as e:
        logger.error(f"Error finding duplicate clients: {e}")
        flash('Erreur lors de la recherche de doublons.', 'danger')
        return redirect(url_for('clients.index'))

@clients_bp.route('/merge/<int:keep_id>/<int:remove_id>', methods=['POST'])
@login_required
@require_role('admin')
@monitor_performance
def perform_merge(keep_id, remove_id):
    """Perform client merge operation"""
    try:
        keep_client = Client.query.get_or_404(keep_id)
        remove_client = Client.query.get_or_404(remove_id)
        
        if keep_client.id == remove_client.id:
            flash('Impossible de fusionner un client avec lui-même.', 'danger')
            return redirect(url_for('clients.merge'))
        
        # Check relationships for the client to be removed
        can_delete, reason, related_counts = ClientService.safe_check_client_relationships(remove_client)
        
        if not can_delete:
            flash(f'Impossible de fusionner: {reason}', 'danger')
            return redirect(url_for('clients.merge'))
        
        # Begin transaction for merge
        try:
            # Update any related records to point to the kept client
            # This depends on your database schema
            
            # Example: Update cheques to point to kept client
            if 'cheques' in related_counts and related_counts['cheques'] > 0:
                # You would need to implement this based on your models
                # db.session.execute(
                #     text("UPDATE cheques SET client_id = :keep_id WHERE client_id = :remove_id"),
                #     {'keep_id': keep_id, 'remove_id': remove_id}
                # )
                pass
            
            # Merge additional data if needed (update kept client with missing info)
            if not keep_client.id_number and remove_client.id_number:
                keep_client.id_number = remove_client.id_number
            
            if not keep_client.vat_number and remove_client.vat_number:
                keep_client.vat_number = remove_client.vat_number
            
            # Delete the redundant client
            remove_name = remove_client.name
            db.session.delete(remove_client)
            db.session.commit()
            
            logger.info(f"Clients merged: '{remove_name}' merged into '{keep_client.name}' by {current_user.username}")
            flash(f'Clients fusionnés avec succès. "{remove_name}" fusionné avec "{keep_client.name}".', 'success')
            
        except Exception as merge_error:
            db.session.rollback()
            logger.error(f"Error during merge operation: {merge_error}")
            flash('Erreur lors de la fusion des clients.', 'danger')
        
        return redirect(url_for('clients.merge'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in merge operation: {e}")
        flash('Erreur lors de la fusion des clients.', 'danger')
        return redirect(url_for('clients.merge'))

@clients_bp.route('/backup')
@login_required
@require_role('admin')
@monitor_performance
def backup_clients():
    """Create a comprehensive backup of all client data"""
    try:
        from datetime import datetime
        import json
        
        # Get all clients with full data
        clients = Client.query.all()
        
        backup_data = {
            'metadata': {
                'created_at': datetime.utcnow().isoformat(),
                'created_by': current_user.username,
                'total_clients': len(clients),
                'version': '1.0'
            },
            'clients': []
        }
        
        for client in clients:
            client_data = {
                'id': client.id,
                'type': client.type,
                'name': client.name,
                'id_number': client.id_number,
                'vat_number': client.vat_number,
                'created_at': client.created_at.isoformat() if hasattr(client, 'created_at') and client.created_at else None,
                'updated_at': client.updated_at.isoformat() if hasattr(client, 'updated_at') and client.updated_at else None
            }
            backup_data['clients'].append(client_data)
        
        # Create JSON response
        from flask import make_response
        response = make_response(json.dumps(backup_data, indent=2, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=clients_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        logger.info(f"Client backup created by {current_user.username} ({len(clients)} records)")
        return response
        
    except Exception as e:
        logger.error(f"Error creating client backup: {e}")
        flash('Erreur lors de la création de la sauvegarde.', 'danger')
        return redirect(url_for('clients.index'))

# Error handlers specific to clients blueprint
@clients_bp.errorhandler(404)
def client_not_found(error):
    flash('Client introuvable.', 'danger')
    return redirect(url_for('clients.index'))

@clients_bp.errorhandler(500)
def client_server_error(error):
    db.session.rollback()
    logger.error(f"Server error in clients module: {error}")
    flash('Erreur serveur dans le module clients.', 'danger')
    return redirect(url_for('clients.index'))

# Context processor for templates
@clients_bp.context_processor
def inject_client_types():
    return {'CLIENT_TYPES': CLIENT_TYPES}