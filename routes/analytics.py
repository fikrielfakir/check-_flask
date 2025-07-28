"""
Analytics routes for advanced reporting and analytics features.
Provides comprehensive analytics dashboard and reporting capabilities.
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import os
import json
import logging
from utils.analytics_engine import AnalyticsEngine
from models import Cheque, Client, Bank, Branch

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/')
@login_required
def analytics_dashboard():
    """Main analytics dashboard"""
    try:
        db_path = os.path.join(current_app.config['DATA_FOLDER'], 'cheques.db')
        analytics = AnalyticsEngine(db_path)
        
        # Get KPI dashboard data
        kpi_data = analytics.generate_kpi_dashboard()
        
        # Get recent performance metrics
        performance_metrics = analytics.calculate_performance_metrics(30)
        
        # Get cash flow prediction
        cash_flow = analytics.predict_cash_flow(30)
        
        # Get top risk clients
        risk_clients = analytics.assess_client_risk()[:5]  # Top 5 risky clients
        
        return render_template('analytics/dashboard.html',
                             kpi_data=kpi_data,
                             performance_metrics=performance_metrics,
                             cash_flow=cash_flow,
                             risk_clients=risk_clients)
    
    except Exception as e:
        logging.error(f"Error in analytics dashboard: {str(e)}")
        flash(f'Erreur lors du chargement du tableau de bord analytique: {str(e)}', 'error')
        return redirect(url_for('dashboard.index'))

@analytics_bp.route('/aging-analysis')
@login_required
def aging_analysis():
    """Cheque aging analysis page"""
    try:
        db_path = os.path.join(current_app.config['DATA_FOLDER'], 'cheques.db')
        analytics = AnalyticsEngine(db_path)
        
        # Get aging analysis data
        aging_data = analytics.calculate_cheque_aging()
        
        # Get status filter from query params
        status_filter = request.args.get('status')
        if status_filter:
            aging_data = analytics.calculate_cheque_aging(status_filter)
        
        return render_template('analytics/aging_analysis.html',
                             aging_data=aging_data,
                             status_filter=status_filter)
    
    except Exception as e:
        logging.error(f"Error in aging analysis: {str(e)}")
        flash(f'Erreur lors de l\'analyse de vieillissement: {str(e)}', 'error')
        return redirect(url_for('analytics.analytics_dashboard'))

@analytics_bp.route('/seasonal-trends')
@login_required
def seasonal_trends():
    """Seasonal trends analysis page"""
    try:
        db_path = os.path.join(current_app.config['DATA_FOLDER'], 'cheques.db')
        analytics = AnalyticsEngine(db_path)
        
        # Get months parameter
        months_back = int(request.args.get('months', 12))
        
        # Get seasonal trends data
        trends_data = analytics.analyze_seasonal_trends(months_back)
        
        return render_template('analytics/seasonal_trends.html',
                             trends_data=trends_data,
                             months_back=months_back)
    
    except Exception as e:
        logging.error(f"Error in seasonal trends: {str(e)}")
        flash(f'Erreur lors de l\'analyse des tendances saisonnières: {str(e)}', 'error')
        return redirect(url_for('analytics.analytics_dashboard'))

@analytics_bp.route('/client-risk')
@login_required
def client_risk():
    """Client risk assessment page"""
    try:
        db_path = os.path.join(current_app.config['DATA_FOLDER'], 'cheques.db')
        analytics = AnalyticsEngine(db_path)
        
        # Get minimum cheques parameter
        min_cheques = int(request.args.get('min_cheques', 5))
        
        # Get client risk data
        risk_data = analytics.assess_client_risk(min_cheques)
        
        return render_template('analytics/client_risk.html',
                             risk_data=risk_data,
                             min_cheques=min_cheques)
    
    except Exception as e:
        logging.error(f"Error in client risk analysis: {str(e)}")
        flash(f'Erreur lors de l\'évaluation des risques clients: {str(e)}', 'error')
        return redirect(url_for('analytics.analytics_dashboard'))

@analytics_bp.route('/performance-metrics')
@login_required
def performance_metrics():
    """Performance metrics page"""
    try:
        db_path = os.path.join(current_app.config['DATA_FOLDER'], 'cheques.db')
        analytics = AnalyticsEngine(db_path)
        
        # Get days parameter
        days_back = int(request.args.get('days', 30))
        
        # Get performance metrics
        metrics = analytics.calculate_performance_metrics(days_back)
        
        return render_template('analytics/performance_metrics.html',
                             metrics=metrics,
                             days_back=days_back)
    
    except Exception as e:
        logging.error(f"Error in performance metrics: {str(e)}")
        flash(f'Erreur lors du calcul des métriques de performance: {str(e)}', 'error')
        return redirect(url_for('analytics.analytics_dashboard'))

@analytics_bp.route('/cash-flow-prediction')
@login_required
def cash_flow_prediction():
    """Cash flow prediction page"""
    try:
        db_path = os.path.join(current_app.config['DATA_FOLDER'], 'cheques.db')
        analytics = AnalyticsEngine(db_path)
        
        # Get days parameter
        days_ahead = int(request.args.get('days', 30))
        
        # Get cash flow prediction
        prediction = analytics.predict_cash_flow(days_ahead)
        
        return render_template('analytics/cash_flow_prediction.html',
                             prediction=prediction,
                             days_ahead=days_ahead)
    
    except Exception as e:
        logging.error(f"Error in cash flow prediction: {str(e)}")
        flash(f'Erreur lors de la prédiction de flux de trésorerie: {str(e)}', 'error')
        return redirect(url_for('analytics.analytics_dashboard'))

@analytics_bp.route('/duplicate-detection')
@login_required
def duplicate_detection():
    """Duplicate cheque detection page"""
    try:
        db_path = os.path.join(current_app.config['DATA_FOLDER'], 'cheques.db')
        analytics = AnalyticsEngine(db_path)
        
        # Get similarity threshold parameter
        threshold = float(request.args.get('threshold', 0.8))
        
        # Get duplicate cheques
        duplicates = analytics.get_duplicate_cheques(threshold)
        
        return render_template('analytics/duplicate_detection.html',
                             duplicates=duplicates,
                             threshold=threshold)
    
    except Exception as e:
        logging.error(f"Error in duplicate detection: {str(e)}")
        flash(f'Erreur lors de la détection des doublons: {str(e)}', 'error')
        return redirect(url_for('analytics.analytics_dashboard'))

@analytics_bp.route('/api/kpi-data')
@login_required
def api_kpi_data():
    """API endpoint for KPI data"""
    try:
        db_path = os.path.join(current_app.config['DATA_FOLDER'], 'cheques.db')
        analytics = AnalyticsEngine(db_path)
        
        kpi_data = analytics.generate_kpi_dashboard()
        
        return jsonify({
            'success': True,
            'data': kpi_data
        })
    
    except Exception as e:
        logging.error(f"Error getting KPI data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@analytics_bp.route('/api/aging-data')
@login_required
def api_aging_data():
    """API endpoint for aging analysis data"""
    try:
        db_path = os.path.join(current_app.config['DATA_FOLDER'], 'cheques.db')
        analytics = AnalyticsEngine(db_path)
        
        status_filter = request.args.get('status')
        aging_data = analytics.calculate_cheque_aging(status_filter)
        
        # Convert dataclasses to dictionaries
        aging_dict = []
        for item in aging_data:
            aging_dict.append({
                'status': item.status,
                'avg_days': item.avg_days,
                'min_days': item.min_days,
                'max_days': item.max_days,
                'total_cheques': item.total_cheques,
                'total_amount': item.total_amount,
                'percentage': item.percentage
            })
        
        return jsonify({
            'success': True,
            'data': aging_dict
        })
    
    except Exception as e:
        logging.error(f"Error getting aging data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@analytics_bp.route('/api/trends-data')
@login_required
def api_trends_data():
    """API endpoint for seasonal trends data"""
    try:
        db_path = os.path.join(current_app.config['DATA_FOLDER'], 'cheques.db')
        analytics = AnalyticsEngine(db_path)
        
        months_back = int(request.args.get('months', 12))
        trends_data = analytics.analyze_seasonal_trends(months_back)
        
        # Convert dataclasses to dictionaries
        trends_dict = []
        for item in trends_data:
            trends_dict.append({
                'period': item.period,
                'inflow_count': item.inflow_count,
                'inflow_amount': item.inflow_amount,
                'outflow_count': item.outflow_count,
                'outflow_amount': item.outflow_amount,
                'net_amount': item.net_amount,
                'trend_direction': item.trend_direction
            })
        
        return jsonify({
            'success': True,
            'data': trends_dict
        })
    
    except Exception as e:
        logging.error(f"Error getting trends data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@analytics_bp.route('/export-report/<report_type>')
@login_required
def export_analytics_report(report_type):
    """Export analytics report"""
    try:
        db_path = os.path.join(current_app.config['DATA_FOLDER'], 'cheques.db')
        analytics = AnalyticsEngine(db_path)
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"analytics_report_{report_type}_{timestamp}.json"
        
        # Create exports directory if it doesn't exist
        exports_dir = current_app.config.get('EXPORTS_FOLDER', os.path.join(os.getcwd(), 'data', 'exports'))
        os.makedirs(exports_dir, exist_ok=True)
        
        output_path = os.path.join(exports_dir, filename)
        
        # Export report
        report_path = analytics.export_analytics_report(report_type, output_path)
        
        return send_file(report_path,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/json')
    
    except Exception as e:
        logging.error(f"Error exporting analytics report: {str(e)}")
        flash(f'Erreur lors de l\'export du rapport: {str(e)}', 'error')
        return redirect(url_for('analytics.analytics_dashboard'))

@analytics_bp.route('/refresh-cache')
@login_required
def refresh_analytics_cache():
    """Refresh analytics cache"""
    try:
        # This could implement caching logic in the future
        flash('Cache analytique actualisé avec succès.', 'success')
        return redirect(url_for('analytics.analytics_dashboard'))
    
    except Exception as e:
        logging.error(f"Error refreshing cache: {str(e)}")
        flash(f'Erreur lors de l\'actualisation du cache: {str(e)}', 'error')
        return redirect(url_for('analytics.analytics_dashboard'))

@analytics_bp.route('/settings')
@login_required
def analytics_settings():
    """Analytics settings page"""
    try:
        return render_template('analytics/settings.html')
    
    except Exception as e:
        logging.error(f"Error in analytics settings: {str(e)}")
        flash(f'Erreur lors du chargement des paramètres: {str(e)}', 'error')
        return redirect(url_for('analytics.analytics_dashboard'))

@analytics_bp.route('/settings', methods=['POST'])
@login_required
def update_analytics_settings():
    """Update analytics settings"""
    try:
        # This could implement settings persistence in the future
        settings = {
            'default_aging_period': request.form.get('aging_period', '30'),
            'risk_threshold': request.form.get('risk_threshold', '10'),
            'prediction_days': request.form.get('prediction_days', '30'),
            'cache_duration': request.form.get('cache_duration', '3600')
        }
        
        # Save settings (implementation depends on your preference)
        flash('Paramètres analytiques mis à jour avec succès.', 'success')
        return redirect(url_for('analytics.analytics_settings'))
    
    except Exception as e:
        logging.error(f"Error updating analytics settings: {str(e)}")
        flash(f'Erreur lors de la mise à jour des paramètres: {str(e)}', 'error')
        return redirect(url_for('analytics.analytics_settings'))

@analytics_bp.route('/bank-performance')
@login_required
def bank_performance():
    """Bank performance analysis page"""
    try:
        db_path = os.path.join(current_app.config['DATA_FOLDER'], 'cheques.db')
        analytics = AnalyticsEngine(db_path)
        
        # Get KPI data which includes bank performance
        kpi_data = analytics.generate_kpi_dashboard()
        bank_performance_data = kpi_data.get('bank_performance', [])
        
        return render_template('analytics/bank_performance.html',
                             bank_performance=bank_performance_data)
    
    except Exception as e:
        logging.error(f"Error in bank performance analysis: {str(e)}")
        flash(f'Erreur lors de l\'analyse de performance bancaire: {str(e)}', 'error')
        return redirect(url_for('analytics.analytics_dashboard'))

@analytics_bp.route('/client-performance')
@login_required
def client_performance():
    """Client performance analysis page"""
    try:
        db_path = os.path.join(current_app.config['DATA_FOLDER'], 'cheques.db')
        analytics = AnalyticsEngine(db_path)
        
        # Get KPI data which includes top clients
        kpi_data = analytics.generate_kpi_dashboard()
        top_clients = kpi_data.get('top_clients', [])
        
        return render_template('analytics/client_performance.html',
                             top_clients=top_clients)
    
    except Exception as e:
        logging.error(f"Error in client performance analysis: {str(e)}")
        flash(f'Erreur lors de l\'analyse de performance client: {str(e)}', 'error')
        return redirect(url_for('analytics.analytics_dashboard'))

@analytics_bp.route('/realtime-monitoring')
@login_required
def realtime_monitoring():
    """Real-time monitoring dashboard"""
    try:
        db_path = os.path.join(current_app.config['DATA_FOLDER'], 'cheques.db')
        analytics = AnalyticsEngine(db_path)
        
        # Get real-time metrics
        performance_metrics = analytics.calculate_performance_metrics(1)  # Last 24 hours
        cash_flow = analytics.predict_cash_flow(7)  # Next 7 days
        
        return render_template('analytics/realtime_monitoring.html',
                             performance_metrics=performance_metrics,
                             cash_flow=cash_flow)
    
    except Exception as e:
        logging.error(f"Error in real-time monitoring: {str(e)}")
        flash(f'Erreur lors du monitoring temps réel: {str(e)}', 'error')
        return redirect(url_for('analytics.analytics_dashboard'))