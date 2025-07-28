from flask import Blueprint, render_template
from flask_login import login_required
from models import Cheque, Client, Bank, Branch
from sqlalchemy import func
from datetime import datetime, timedelta
from app import db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    # Statistics for dashboard widgets
    today = datetime.now().date()
    this_month_start = today.replace(day=1)
    
    # Total cheques by status
    status_counts = db.session.query(
        Cheque.status,
        func.count(Cheque.id).label('count')
    ).group_by(Cheque.status).all()
    
    status_stats = {status: count for status, count in status_counts}
    
    # Total amount collected this month
    monthly_amount = db.session.query(
        func.sum(Cheque.amount)
    ).filter(
        Cheque.status == 'encaisse',
        Cheque.updated_at >= this_month_start
    ).scalar() or 0
    
    # Overdue cheques
    overdue_cheques = Cheque.query.filter(
        Cheque.due_date < today,
        Cheque.status.in_(['en_attente', 'depose'])
    ).count()
    
    # Cheques due in next 3 days
    due_soon = Cheque.query.filter(
        Cheque.due_date.between(today, today + timedelta(days=3)),
        Cheque.status.in_(['en_attente', 'depose'])
    ).count()
    
    # Top 5 clients with rejected cheques
    rejected_clients = db.session.query(
        Client.name,
        func.count(Cheque.id).label('rejected_count')
    ).join(Cheque).filter(
        Cheque.status == 'rejete'
    ).group_by(Client.id, Client.name).order_by(
        func.count(Cheque.id).desc()
    ).limit(5).all()
    
    # Recent cheques
    recent_cheques = Cheque.query.order_by(
        Cheque.created_at.desc()
    ).limit(10).all()
    
    return render_template('dashboard/index.html',
                         status_stats=status_stats,
                         monthly_amount=monthly_amount,
                         overdue_cheques=overdue_cheques,
                         due_soon=due_soon,
                         rejected_clients=rejected_clients,
                         recent_cheques=recent_cheques)
