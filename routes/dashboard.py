from flask import Blueprint, render_template
from flask_login import login_required
from models import Cheque, Client, Bank, Branch
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from app import db
import json

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    # Current date and month start
    today = datetime.now().date()
    this_month_start = today.replace(day=1)
    
    # -------------------------
    # 1. Total cheques by status
    # -------------------------
    status_counts = db.session.query(
        Cheque.status,
        func.count(Cheque.id).label('count')
    ).group_by(Cheque.status).all()
    
    status_stats = {status: count for status, count in status_counts}
    
    # -------------------------
    # 2. Total amount collected this month
    # -------------------------
    monthly_amount = db.session.query(
        func.sum(Cheque.amount)
    ).filter(
        Cheque.status == 'ENCAISSE',
        Cheque.updated_at >= this_month_start
    ).scalar() or 0
    
    # -------------------------
    # 3. Overdue and due soon cheques
    # -------------------------
    overdue_cheques = Cheque.query.filter(
        Cheque.due_date < today,
        Cheque.status.in_(['EN ATTENTE'])
    ).count()
    
    due_soon = Cheque.query.filter(
        Cheque.due_date.between(today, today + timedelta(days=3)),
        Cheque.status.in_(['EN ATTENTE'])
    ).count()
    
    # -------------------------
    # 4. Monthly evolution data (last 6 months)
    # -------------------------
    monthly_labels = []
    monthly_amounts = []
    
    for i in range(5, -1, -1):
        month_date = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_end = month_date.replace(day=28) + timedelta(days=4)
        month_end = month_end - timedelta(days=month_end.day)
        
        amount = db.session.query(
            func.sum(Cheque.amount)
        ).filter(
            Cheque.status == 'ENCAISSE',
            Cheque.updated_at >= month_date,
            Cheque.updated_at <= month_end
        ).scalar() or 0
        
        monthly_labels.append(month_date.strftime('%m/%Y'))
        monthly_amounts.append(float(amount))
    
    # -------------------------
    # 5. Top 5 clients by encashed amount (FIXED)
    # -------------------------
    top_clients = db.session.query(
        Client.name,
        func.sum(Cheque.amount).label('total_amount')
    ).join(Cheque).filter(
        Cheque.status == 'ENCAISSE'
    ).group_by(Client.id, Client.name).order_by(
        func.sum(Cheque.amount).desc()
    ).limit(5).all()
    
    # top_clients returns [(name, total_amount), ...]
    top_clients_names = [
        name[:20] + '...' if len(name) > 20 else name
        for name, _ in top_clients
    ]
    top_clients_amounts = [float(amount) for _, amount in top_clients]
    
    # -------------------------
    # 6. Bank distribution
    # -------------------------
    bank_data = db.session.query(
        Bank.name,
        func.count(Cheque.id).label('cheque_count')
    ).select_from(Bank).join(Branch).join(Cheque).group_by(Bank.id, Bank.name).order_by(
        func.count(Cheque.id).desc()
    ).all()
    
    bank_names = [bank for bank, _ in bank_data]
    bank_cheque_counts = [count for _, count in bank_data]
    
    # -------------------------
    # 7. Risk clients (>=2 unpaid cheques)
    # -------------------------
    risk_clients_data = db.session.query(
        Client.id,
        Client.name,
        func.count(Cheque.id).label('unpaid_count'),
        func.sum(Cheque.amount).label('unpaid_amount')
    ).join(Cheque).filter(
        Cheque.status == 'IMPAYE'
    ).group_by(Client.id, Client.name).having(
        func.count(Cheque.id) >= 2
    ).order_by(func.sum(Cheque.amount).desc()).all()
    
    risk_clients = []
    for client_id, client_name, unpaid_count, unpaid_amount in risk_clients_data:
        risk_clients.append({
            'id': client_id,
            'name': client_name,
            'unpaid_count': unpaid_count,
            'unpaid_amount': float(unpaid_amount or 0)
        })
    
    # -------------------------
    # 8. Recent cheques
    # -------------------------
    recent_cheques = Cheque.query.order_by(
        Cheque.created_at.desc()
    ).limit(15).all()
    
    # -------------------------
    # 9. Alert cheques (overdue or due soon)
    # -------------------------
    alert_cheques = Cheque.query.filter(
        or_(
            and_(Cheque.due_date < today, Cheque.status == 'EN ATTENTE'),
            and_(
                Cheque.due_date.between(today, today + timedelta(days=3)), 
                Cheque.status == 'EN ATTENTE'
            )
        )
    ).order_by(Cheque.due_date).limit(10).all()
    
    # Add days overdue to alert cheques
    for cheque in alert_cheques:
        cheque.days_overdue = (today - cheque.due_date).days if cheque.due_date < today else 0
    
    # -------------------------
    # 10. Render template with JSON for charts
    # -------------------------
    return render_template(
        'dashboard/enhanced_index.html',
        status_stats=status_stats,
        monthly_amount=monthly_amount,
        overdue_cheques=overdue_cheques,
        due_soon=due_soon,
        monthly_labels=json.dumps(monthly_labels),
        monthly_amounts=json.dumps(monthly_amounts),
        top_clients_names=json.dumps(top_clients_names),
        top_clients_amounts=json.dumps(top_clients_amounts),
        bank_names=json.dumps(bank_names),
        bank_cheque_counts=json.dumps(bank_cheque_counts),
        risk_clients=risk_clients,
        recent_cheques=recent_cheques,
        alert_cheques=alert_cheques
    )
