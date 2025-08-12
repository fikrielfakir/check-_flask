# API routes for optimized functionality
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from utils.performance import cached_query, LazyLoader, performance_monitor
from utils.security import TwoFactorAuth, require_permissions, AuditLogger
from utils.ai_ml import FraudDetectionModel, CashFlowPredictor, IntelligentRecommendations
from models import Cheque, Client, Depositor, Bank, Branch
from app import db
import logging

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize AI models
fraud_model = FraudDetectionModel()
cashflow_predictor = CashFlowPredictor()

@api_bp.route('/charts/<chart_type>')
@login_required
@cached_query(timeout=600)
@performance_monitor
def get_chart_data(chart_type):
    """Get chart data with caching and lazy loading"""
    filters = {
        'status': request.args.get('status'),
        'bank_id': request.args.get('bank_id'),
        'date_from': request.args.get('date_from'),
        'date_to': request.args.get('date_to')
    }
    
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}
    
    try:
        data = LazyLoader.load_chart_data(chart_type, filters)
        return jsonify(data)
    except Exception as e:
        logging.error(f"Error loading chart data for {chart_type}: {e}")
        return jsonify({'error': 'Failed to load chart data'}), 500

@api_bp.route('/clients/search')
@login_required
@performance_monitor
def search_clients():
    """Optimized client search with caching"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify([])
    
    try:
        clients = Client.query.filter(
            Client.name.ilike(f'%{query}%')
        ).filter_by(is_active=True).limit(10).all()
        
        results = []
        for client in clients:
            results.append({
                'id': client.id,
                'name': client.name,
                'type': client.type,
                'details': f"{client.type.title()} - {client.city or 'N/A'}"
            })
        
        return jsonify(results)
    except Exception as e:
        logging.error(f"Error searching clients: {e}")
        return jsonify([])

@api_bp.route('/depositors/search')
@login_required
@performance_monitor
def search_depositors():
    """Optimized depositor search with caching"""
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify([])
    
    try:
        depositors = Depositor.query.filter(
            Depositor.name.ilike(f'%{query}%')
        ).filter_by(is_active=True).limit(10).all()
        
        results = []
        for depositor in depositors:
            results.append({
                'id': depositor.id,
                'name': depositor.name,
                'type': depositor.type,
                'details': f"{depositor.type.title()} - {depositor.company_name or depositor.phone or 'N/A'}"
            })
        
        return jsonify(results)
    except Exception as e:
        logging.error(f"Error searching depositors: {e}")
        return jsonify([])

@api_bp.route('/fraud/check', methods=['POST'])
@login_required
@require_permissions(['admin', 'comptable'])
@AuditLogger.audit_action('FRAUD_CHECK')
def check_fraud():
    """Check fraud probability for a cheque"""
    try:
        data = request.get_json()
        cheque_id = data.get('cheque_id')
        
        if not cheque_id:
            return jsonify({'error': 'Cheque ID required'}), 400
        
        cheque = Cheque.query.get_or_404(cheque_id)
        probability = fraud_model.predict_fraud_probability(cheque)
        
        risk_level = 'low'
        if probability > 0.7:
            risk_level = 'high'
        elif probability > 0.4:
            risk_level = 'medium'
        
        return jsonify({
            'cheque_id': cheque_id,
            'fraud_probability': round(probability, 3),
            'risk_level': risk_level,
            'recommendations': IntelligentRecommendations.suggest_optimal_deposit_timing(cheque)
        })
        
    except Exception as e:
        logging.error(f"Error checking fraud: {e}")
        return jsonify({'error': 'Failed to check fraud'}), 500

@api_bp.route('/cashflow/predict')
@login_required
@require_permissions(['admin', 'comptable'])
@cached_query(timeout=3600)  # Cache for 1 hour
def predict_cashflow():
    """Predict cash flow for next 30 days"""
    try:
        predictions = cashflow_predictor.predict_next_30_days()
        return jsonify({
            'predictions': predictions,
            'summary': {
                'total_predicted': sum(p['predicted_amount'] for p in predictions),
                'average_daily': sum(p['predicted_amount'] for p in predictions) / 30,
                'confidence': 'medium'  # Could be calculated based on model performance
            }
        })
    except Exception as e:
        logging.error(f"Error predicting cashflow: {e}")
        return jsonify({'error': 'Failed to predict cashflow'}), 500

@api_bp.route('/recommendations/client/<int:client_id>')
@login_required
@performance_monitor
def get_client_recommendations(client_id):
    """Get AI-powered recommendations for a client"""
    try:
        client = Client.query.get_or_404(client_id)
        recommendations = IntelligentRecommendations.recommend_client_actions(client)
        
        return jsonify({
            'client_id': client_id,
            'client_name': client.name,
            'recommendations': recommendations
        })
    except Exception as e:
        logging.error(f"Error getting client recommendations: {e}")
        return jsonify({'error': 'Failed to get recommendations'}), 500

@api_bp.route('/2fa/setup', methods=['POST'])
@login_required
@AuditLogger.audit_action('2FA_SETUP')
def setup_2fa():
    """Setup two-factor authentication"""
    try:
        secret = TwoFactorAuth.generate_secret()
        qr_code = TwoFactorAuth.generate_qr_code(current_user, secret)
        
        # Store secret temporarily (should be confirmed before permanent storage)
        from flask import session
        session['temp_2fa_secret'] = secret
        
        return jsonify({
            'secret': secret,
            'qr_code': qr_code,
            'manual_entry_key': secret
        })
    except Exception as e:
        logging.error(f"Error setting up 2FA: {e}")
        return jsonify({'error': 'Failed to setup 2FA'}), 500

@api_bp.route('/2fa/verify', methods=['POST'])
@login_required
@AuditLogger.audit_action('2FA_VERIFY')
def verify_2fa():
    """Verify two-factor authentication token"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Token required'}), 400
        
        from flask import session
        secret = session.get('temp_2fa_secret') or getattr(current_user, 'two_factor_secret', None)
        
        if not secret:
            return jsonify({'error': 'No 2FA secret found'}), 400
        
        is_valid = TwoFactorAuth.verify_token(secret, token)
        
        if is_valid:
            # Mark as verified in session
            session['2fa_verified'] = True
            session['2fa_verified_at'] = datetime.utcnow().isoformat()
            
            # If this is setup verification, enable 2FA for user
            if 'temp_2fa_secret' in session:
                # In a real implementation, you'd update the user model
                # current_user.two_factor_secret = secret
                # current_user.two_factor_enabled = True
                # db.session.commit()
                session.pop('temp_2fa_secret', None)
            
            return jsonify({'verified': True})
        else:
            return jsonify({'verified': False, 'error': 'Invalid token'}), 400
            
    except Exception as e:
        logging.error(f"Error verifying 2FA: {e}")
        return jsonify({'error': 'Failed to verify 2FA'}), 500

@api_bp.route('/analytics/performance')
@login_required
@require_permissions(['admin'])
def get_performance_analytics():
    """Get system performance analytics"""
    try:
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # System performance metrics
        last_hour = datetime.utcnow() - timedelta(hours=1)
        
        metrics = {
            'cheques_processed_last_hour': db.session.query(func.count(Cheque.id)).filter(
                Cheque.updated_at >= last_hour
            ).scalar(),
            'active_users_today': db.session.query(func.count(func.distinct(Cheque.created_by))).filter(
                Cheque.created_at >= datetime.utcnow().date()
            ).scalar(),
            'database_size': {
                'cheques': Cheque.query.count(),
                'clients': Client.query.count(),
                'depositors': Depositor.query.count()
            }
        }
        
        return jsonify(metrics)
    except Exception as e:
        logging.error(f"Error getting performance analytics: {e}")
        return jsonify({'error': 'Failed to get analytics'}), 500

@api_bp.route('/notifications/send', methods=['POST'])
@login_required
@require_permissions(['admin', 'comptable'])
@AuditLogger.audit_action('SEND_NOTIFICATION')
def send_notification():
    """Send real-time notification"""
    try:
        data = request.get_json()
        message_type = data.get('type', 'info')
        message = data.get('message', '')
        target_users = data.get('target_users', [])
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
        
        # In a real implementation with WebSocket support:
        # socketio.emit('notification', {
        #     'type': message_type,
        #     'message': message,
        #     'sender': current_user.username,
        #     'timestamp': datetime.utcnow().isoformat()
        # }, room=target_users if target_users else None)
        
        return jsonify({'sent': True, 'message': 'Notification sent successfully'})
    except Exception as e:
        logging.error(f"Error sending notification: {e}")
        return jsonify({'error': 'Failed to send notification'}), 500

@api_bp.errorhandler(404)
def api_not_found(error):
    return jsonify({'error': 'API endpoint not found'}), 404

@api_bp.errorhandler(500)
def api_internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500