"""
Advanced Analytics Routes for Enhanced Cheque Management System
Provides comprehensive analytics, reporting, and dashboard capabilities
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from app import db
from models import Cheque, Client, User, AuditLog
from utils.advanced_analytics import AdvancedAnalyticsEngine
from utils.smart_automation import SmartAutomationEngine, WorkflowManager
import json

advanced_analytics_bp = Blueprint('advanced_analytics', __name__)

@advanced_analytics_bp.route('/executive-dashboard')
@login_required
def executive_dashboard():
    """Executive dashboard with comprehensive KPIs and analytics"""
    if current_user.role not in ['admin', 'manager']:
        flash('Accès non autorisé', 'error')
        return redirect(url_for('dashboard.index'))
    
    analytics = AdvancedAnalyticsEngine(db.session)
    dashboard_data = analytics.generate_executive_dashboard_data()
    
    return render_template('analytics/executive_dashboard.html', 
                         dashboard_data=dashboard_data,
                         current_user=current_user)

@advanced_analytics_bp.route('/cheque-aging')
@login_required
def cheque_aging_analysis():
    """Comprehensive cheque aging analysis"""
    analytics = AdvancedAnalyticsEngine(db.session)
    
    # Get date range from request
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    aging_data = analytics.get_cheque_aging_analysis(start_date, end_date)
    
    return render_template('analytics/cheque_aging.html',
                         aging_data=aging_data,
                         start_date=start_date,
                         end_date=end_date)

@advanced_analytics_bp.route('/seasonal-trends')
@login_required
def seasonal_trends():
    """Seasonal trends analysis for cheque inflow/outflow"""
    analytics = AdvancedAnalyticsEngine(db.session)
    years = int(request.args.get('years', 2))
    
    trends_data = analytics.analyze_seasonal_trends(years)
    
    return render_template('analytics/seasonal_trends.html',
                         trends_data=trends_data,
                         years=years)

@advanced_analytics_bp.route('/risk-assessment')
@login_required
def risk_assessment():
    """Client risk assessment dashboard"""
    analytics = AdvancedAnalyticsEngine(db.session)
    client_id = request.args.get('client_id')
    
    risk_data = analytics.assess_client_risk(client_id)
    
    return render_template('analytics/risk_assessment.html',
                         risk_data=risk_data,
                         selected_client_id=client_id)

@advanced_analytics_bp.route('/performance-metrics')
@login_required
def performance_metrics():
    """Performance metrics for users and system"""
    analytics = AdvancedAnalyticsEngine(db.session)
    
    user_id = request.args.get('user_id')
    period_days = int(request.args.get('period_days', 30))
    
    metrics = analytics.calculate_performance_metrics(user_id, period_days)
    
    # Get all users for filter dropdown
    users = User.query.filter(User.is_active == True).all()
    
    return render_template('analytics/performance_metrics.html',
                         metrics=metrics,
                         users=users,
                         selected_user_id=user_id,
                         period_days=period_days)

@advanced_analytics_bp.route('/cash-flow-prediction')
@login_required
def cash_flow_prediction():
    """Cash flow prediction based on pending cheques"""
    analytics = AdvancedAnalyticsEngine(db.session)
    
    days_ahead = int(request.args.get('days_ahead', 30))
    cash_flow = analytics.predict_cash_flow(days_ahead)
    
    return render_template('analytics/cash_flow_prediction.html',
                         cash_flow=cash_flow,
                         days_ahead=days_ahead)

@advanced_analytics_bp.route('/anomaly-detection')
@login_required
def anomaly_detection():
    """Anomaly and fraud detection dashboard"""
    if current_user.role not in ['admin', 'manager']:
        flash('Accès non autorisé', 'error')
        return redirect(url_for('dashboard.index'))
    
    analytics = AdvancedAnalyticsEngine(db.session)
    anomalies = analytics.detect_anomalies()
    
    return render_template('analytics/anomaly_detection.html',
                         anomalies=anomalies)

@advanced_analytics_bp.route('/smart-automation')
@login_required
def smart_automation_dashboard():
    """Smart automation control panel"""
    if current_user.role not in ['admin', 'manager']:
        flash('Accès non autorisé', 'error')
        return redirect(url_for('dashboard.index'))
    
    automation = SmartAutomationEngine(db.session)
    
    return render_template('analytics/smart_automation.html')

@advanced_analytics_bp.route('/api/run-duplicate-detection', methods=['POST'])
@login_required
def run_duplicate_detection():
    """API endpoint to run duplicate detection"""
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    automation = SmartAutomationEngine(db.session)
    results = automation.detect_duplicate_cheques()
    
    # Log the action
    audit_log = AuditLog(
        user_id=current_user.id,
        action='run_duplicate_detection',
        new_values=json.dumps({'results': results})
    )
    db.session.add(audit_log)
    db.session.commit()
    
    return jsonify(results)

@advanced_analytics_bp.route('/api/auto-assign-cheques', methods=['POST'])
@login_required
def auto_assign_cheques():
    """API endpoint to auto-assign cheques"""
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    automation = SmartAutomationEngine(db.session)
    strategy = request.json.get('strategy', 'balanced')
    
    results = automation.auto_assign_cheques(strategy)
    
    # Log the action
    audit_log = AuditLog(
        user_id=current_user.id,
        action='auto_assign_cheques',
        new_values=json.dumps({'strategy': strategy, 'results': results})
    )
    db.session.add(audit_log)
    db.session.commit()
    
    return jsonify(results)

@advanced_analytics_bp.route('/api/auto-prioritize', methods=['POST'])
@login_required
def auto_prioritize():
    """API endpoint to auto-prioritize cheques"""
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    automation = SmartAutomationEngine(db.session)
    results = automation.auto_prioritize_cheques()
    
    # Log the action
    audit_log = AuditLog(
        user_id=current_user.id,
        action='auto_prioritize_cheques',
        new_values=json.dumps({'results': results})
    )
    db.session.add(audit_log)
    db.session.commit()
    
    return jsonify(results)

@advanced_analytics_bp.route('/api/send-reminders', methods=['POST'])
@login_required
def send_automated_reminders():
    """API endpoint to send automated reminders"""
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    automation = SmartAutomationEngine(db.session)
    test_mode = request.json.get('test_mode', True)
    
    results = automation.auto_send_reminders(test_mode)
    
    # Log the action
    audit_log = AuditLog(
        user_id=current_user.id,
        action='send_automated_reminders',
        new_values=json.dumps({'test_mode': test_mode, 'results': results})
    )
    db.session.add(audit_log)
    db.session.commit()
    
    return jsonify(results)

@advanced_analytics_bp.route('/api/calculate-penalties', methods=['POST'])
@login_required
def calculate_penalties():
    """API endpoint to calculate penalties"""
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    automation = SmartAutomationEngine(db.session)
    results = automation.auto_calculate_penalties()
    
    # Log the action
    audit_log = AuditLog(
        user_id=current_user.id,
        action='calculate_penalties',
        new_values=json.dumps({'results': results})
    )
    db.session.add(audit_log)
    db.session.commit()
    
    return jsonify(results)

@advanced_analytics_bp.route('/api/update-risk-assessments', methods=['POST'])
@login_required
def update_risk_assessments():
    """API endpoint to update client risk assessments"""
    if current_user.role not in ['admin', 'manager']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    automation = SmartAutomationEngine(db.session)
    results = automation.auto_risk_assessment_update()
    
    # Log the action
    audit_log = AuditLog(
        user_id=current_user.id,
        action='update_risk_assessments',
        new_values=json.dumps({'results': results})
    )
    db.session.add(audit_log)
    db.session.commit()
    
    return jsonify(results)

# Workflow Management Routes
@advanced_analytics_bp.route('/workflow-management')
@login_required
def workflow_management():
    """Workflow management dashboard"""
    if current_user.role not in ['admin', 'manager']:
        flash('Accès non autorisé', 'error')
        return redirect(url_for('dashboard.index'))
    
    workflow_manager = WorkflowManager(db.session)
    
    return render_template('analytics/workflow_management.html')

@advanced_analytics_bp.route('/api/execute-workflow', methods=['POST'])
@login_required
def execute_workflow():
    """API endpoint to execute workflow action"""
    cheque_id = request.json.get('cheque_id')
    action = request.json.get('action')
    
    if not cheque_id or not action:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    workflow_manager = WorkflowManager(db.session)
    result = workflow_manager.execute_workflow(cheque_id, action)
    
    if 'error' not in result:
        # Log the workflow action
        audit_log = AuditLog(
            user_id=current_user.id,
            action=f'workflow_{action}',
            table_name='cheques',
            record_id=cheque_id,
            new_values=json.dumps(result)
        )
        db.session.add(audit_log)
        db.session.commit()
    
    return jsonify(result)

# Chart and Data API Endpoints
@advanced_analytics_bp.route('/api/chart-data/aging-distribution')
@login_required
def aging_distribution_chart():
    """API endpoint for aging distribution chart data"""
    analytics = AdvancedAnalyticsEngine(db.session)
    aging_data = analytics.get_cheque_aging_analysis()
    
    chart_data = {
        'labels': list(aging_data['age_group_distribution'].keys()),
        'data': list(aging_data['age_group_distribution'].values()),
        'backgroundColor': [
            '#28a745', '#ffc107', '#fd7e14', '#dc3545', '#6c757d'
        ]
    }
    
    return jsonify(chart_data)

@advanced_analytics_bp.route('/api/chart-data/status-breakdown')
@login_required
def status_breakdown_chart():
    """API endpoint for status breakdown chart data"""
    analytics = AdvancedAnalyticsEngine(db.session)
    aging_data = analytics.get_cheque_aging_analysis()
    
    chart_data = {
        'labels': list(aging_data['status_distribution'].keys()),
        'data': list(aging_data['status_distribution'].values()),
        'backgroundColor': [
            '#6c757d', '#28a745', '#dc3545', '#ffc107', '#007bff', '#6f42c1'
        ]
    }
    
    return jsonify(chart_data)

@advanced_analytics_bp.route('/api/chart-data/monthly-trends')
@login_required
def monthly_trends_chart():
    """API endpoint for monthly trends chart data"""
    analytics = AdvancedAnalyticsEngine(db.session)
    trends = analytics.analyze_seasonal_trends()
    
    # Process monthly trends data for chart
    monthly_data = trends['monthly_trends']
    
    # Simplify for demo - in production, process the complex nested data structure
    chart_data = {
        'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'datasets': [
            {
                'label': 'Montant Total',
                'data': [100000, 120000, 95000, 110000, 130000, 85000, 140000, 125000, 115000, 135000, 90000, 105000],
                'borderColor': '#007bff',
                'backgroundColor': 'rgba(0, 123, 255, 0.1)'
            }
        ]
    }
    
    return jsonify(chart_data)

@advanced_analytics_bp.route('/api/chart-data/risk-distribution')
@login_required
def risk_distribution_chart():
    """API endpoint for client risk distribution chart"""
    analytics = AdvancedAnalyticsEngine(db.session)
    risk_data = analytics.assess_client_risk()
    
    distribution = risk_data['risk_distribution']
    
    chart_data = {
        'labels': ['Faible Risque', 'Risque Moyen', 'Risque Élevé'],
        'data': [distribution['low'], distribution['medium'], distribution['high']],
        'backgroundColor': ['#28a745', '#ffc107', '#dc3545']
    }
    
    return jsonify(chart_data)

@advanced_analytics_bp.route('/api/kpi-summary')
@login_required
def kpi_summary():
    """API endpoint for KPI summary data"""
    analytics = AdvancedAnalyticsEngine(db.session)
    dashboard_data = analytics.generate_executive_dashboard_data()
    
    return jsonify(dashboard_data['kpi_summary'])

@advanced_analytics_bp.route('/audit-log')
@login_required
def audit_log():
    """Audit log viewer for compliance and security"""
    if current_user.role not in ['admin']:
        flash('Accès non autorisé', 'error')
        return redirect(url_for('dashboard.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('analytics/audit_log.html', logs=logs)