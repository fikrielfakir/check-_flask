from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Client
from forms import ClientForm
from app import db
from sqlalchemy import or_

clients_bp = Blueprint('clients', __name__)

def check_access():
    """Check if current user has access to manage clients"""
    if current_user.role not in ['admin', 'comptable', 'agent']:
        flash('Accès refusé.', 'danger')
        return False
    return True

@clients_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '')
    client_type = request.args.get('type', '')
    
    query = Client.query
    
    if search:
        query = query.filter(
            or_(
                Client.name.contains(search),
                Client.id_number.contains(search),
                Client.vat_number.contains(search)
            )
        )
    
    if client_type:
        query = query.filter(Client.type == client_type)
    
    clients = query.order_by(Client.name).all()
    
    return render_template('clients/index.html', 
                         clients=clients, 
                         search=search, 
                         client_type=client_type)

@clients_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if not check_access():
        return redirect(url_for('clients.index'))
    
    form = ClientForm()
    if form.validate_on_submit():
        client = Client(
            type=form.type.data,
            name=form.name.data,
            id_number=form.id_number.data,
            vat_number=form.vat_number.data
        )
        db.session.add(client)
        db.session.commit()
        flash('Client ajouté avec succès!', 'success')
        return redirect(url_for('clients.index'))
    
    return render_template('clients/form.html', form=form, title='Nouveau Client')

@clients_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if not check_access():
        return redirect(url_for('clients.index'))
    
    client = Client.query.get_or_404(id)
    form = ClientForm(obj=client)
    
    if form.validate_on_submit():
        client.type = form.type.data
        client.name = form.name.data
        client.id_number = form.id_number.data
        client.vat_number = form.vat_number.data
        db.session.commit()
        flash('Client modifié avec succès!', 'success')
        return redirect(url_for('clients.index'))
    
    return render_template('clients/form.html', form=form, title='Modifier Client', client=client)

@clients_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    if current_user.role != 'admin':
        flash('Seuls les administrateurs peuvent supprimer des clients.', 'danger')
        return redirect(url_for('clients.index'))
    
    client = Client.query.get_or_404(id)
    
    # Check if client has associated cheques
    if client.cheques:
        flash('Impossible de supprimer ce client car il a des chèques associés.', 'danger')
        return redirect(url_for('clients.index'))
    
    db.session.delete(client)
    db.session.commit()
    flash('Client supprimé avec succès!', 'success')
    return redirect(url_for('clients.index'))

@clients_bp.route('/api/search')
@login_required
def api_search():
    """API endpoint for client autocomplete"""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    clients = Client.query.filter(
        or_(
            Client.name.contains(query),
            Client.id_number.contains(query),
            Client.vat_number.contains(query)
        )
    ).limit(10).all()
    
    return jsonify([{
        'id': client.id,
        'name': client.name,
        'type': client.type,
        'id_number': client.id_number,
        'vat_number': client.vat_number
    } for client in clients])

@clients_bp.route('/api/create', methods=['POST'])
@login_required
def api_create():
    """API endpoint to create a new client"""
    if not check_access():
        return jsonify({'error': 'Accès refusé'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if not data.get('name') or not data.get('type'):
        return jsonify({'error': 'Nom et type sont requis'}), 400
    
    # Check if client already exists
    existing = Client.query.filter_by(name=data['name']).first()
    if existing:
        return jsonify({'error': 'Un client avec ce nom existe déjà'}), 400
    
    client = Client(
        type=data['type'],
        name=data['name'],
        id_number=data.get('id_number', ''),
        vat_number=data.get('vat_number', '')
    )
    
    db.session.add(client)
    db.session.commit()
    
    return jsonify({
        'id': client.id,
        'name': client.name,
        'type': client.type,
        'id_number': client.id_number,
        'vat_number': client.vat_number
    })
