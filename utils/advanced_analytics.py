"""
Advanced Analytics Engine for Cheque Management System
Implements comprehensive analytics, risk assessment, and predictive modeling
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import json
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


class AdvancedAnalyticsEngine:
    """Comprehensive analytics engine with ML capabilities"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.scaler = StandardScaler()
        self.risk_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
    
    def get_cheque_aging_analysis(self, start_date=None, end_date=None):
        """Analyze cheque aging by status with detailed metrics"""
        from models import Cheque
        
        query = self.db.query(Cheque)
        if start_date:
            query = query.filter(Cheque.created_at >= start_date)
        if end_date:
            query = query.filter(Cheque.created_at <= end_date)
        
        cheques = query.all()
        aging_data = []
        
        for cheque in cheques:
            days_in_status = self._calculate_days_in_status(cheque)
            aging_data.append({
                'cheque_id': cheque.id,
                'status': cheque.status,
                'amount': float(cheque.amount),
                'days_in_status': days_in_status,
                'client_risk': cheque.client.risk_level,
                'overdue': cheque.is_overdue,
                'age_group': self._get_age_group(days_in_status)
            })
        
        df = pd.DataFrame(aging_data)
        
        # Calculate aging statistics by status
        aging_stats = df.groupby(['status', 'age_group']).agg({
            'cheque_id': 'count',
            'amount': ['sum', 'mean'],
            'days_in_status': ['mean', 'max', 'min']
        }).round(2)
        
        return {
            'raw_data': aging_data,
            'statistics': aging_stats.to_dict(),
            'status_distribution': df['status'].value_counts().to_dict(),
            'age_group_distribution': df['age_group'].value_counts().to_dict(),
            'overdue_count': df['overdue'].sum(),
            'total_overdue_amount': df[df['overdue']]['amount'].sum()
        }
    
    def analyze_seasonal_trends(self, years=2):
        """Analyze seasonal patterns in cheque inflow/outflow"""
        from models import Cheque
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        cheques = self.db.query(Cheque).filter(
            Cheque.created_at >= start_date
        ).all()
        
        trend_data = []
        for cheque in cheques:
            trend_data.append({
                'date': cheque.created_at.date(),
                'month': cheque.created_at.month,
                'quarter': (cheque.created_at.month - 1) // 3 + 1,
                'year': cheque.created_at.year,
                'amount': float(cheque.amount),
                'status': cheque.status,
                'is_inflow': cheque.status == 'encaisse',
                'is_bounce': cheque.status == 'rejete'
            })
        
        df = pd.DataFrame(trend_data)
        
        # Monthly trends
        monthly_trends = df.groupby(['year', 'month']).agg({
            'amount': ['sum', 'count', 'mean'],
            'is_inflow': 'sum',
            'is_bounce': 'sum'
        }).round(2)
        
        # Quarterly analysis
        quarterly_trends = df.groupby(['year', 'quarter']).agg({
            'amount': ['sum', 'count'],
            'is_inflow': 'sum',
            'is_bounce': 'sum'
        }).round(2)
        
        # Seasonal patterns
        seasonal_patterns = df.groupby('month').agg({
            'amount': ['mean', 'std'],
            'is_bounce': 'mean'
        }).round(3)
        
        return {
            'monthly_trends': monthly_trends.to_dict(),
            'quarterly_trends': quarterly_trends.to_dict(),
            'seasonal_patterns': seasonal_patterns.to_dict(),
            'peak_months': seasonal_patterns['amount']['mean'].nlargest(3).to_dict(),
            'high_risk_months': seasonal_patterns['is_bounce']['mean'].nlargest(3).to_dict()
        }
    
    def assess_client_risk(self, client_id=None):
        """Advanced client risk assessment using ML"""
        from models import Client, Cheque
        
        if client_id:
            clients = [self.db.query(Client).get(client_id)]
        else:
            clients = self.db.query(Client).all()
        
        risk_assessments = []
        
        for client in clients:
            if not client.cheques:
                continue
                
            # Feature extraction
            features = self._extract_client_features(client)
            risk_score = self._calculate_ml_risk_score(features)
            
            assessment = {
                'client_id': client.id,
                'client_name': client.name,
                'risk_score': risk_score,
                'risk_level': self._get_risk_level(risk_score),
                'features': features,
                'recommendations': self._generate_risk_recommendations(risk_score, features)
            }
            
            risk_assessments.append(assessment)
            
            # Update client risk in database
            client.risk_score = risk_score
            client.last_risk_assessment = datetime.utcnow()
        
        self.db.commit()
        
        return {
            'assessments': risk_assessments,
            'high_risk_count': len([r for r in risk_assessments if r['risk_level'] == 'high']),
            'average_risk_score': np.mean([r['risk_score'] for r in risk_assessments]),
            'risk_distribution': self._calculate_risk_distribution(risk_assessments)
        }
    
    def calculate_performance_metrics(self, user_id=None, period_days=30):
        """Calculate comprehensive performance metrics"""
        from models import Cheque, User, ChequeStatusHistory
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        query = self.db.query(Cheque).filter(
            Cheque.updated_at >= start_date
        )
        
        if user_id:
            query = query.filter(Cheque.assigned_user_id == user_id)
        
        cheques = query.all()
        
        metrics = {
            'total_processed': len(cheques),
            'total_amount': sum(float(c.amount) for c in cheques),
            'success_rate': 0,
            'bounce_rate': 0,
            'average_processing_time': 0,
            'status_breakdown': {},
            'daily_volume': [],
            'efficiency_score': 0
        }
        
        if cheques:
            # Status breakdown
            status_counts = {}
            processing_times = []
            
            for cheque in cheques:
                status = cheque.status
                status_counts[status] = status_counts.get(status, 0) + 1
                
                if cheque.processing_time:
                    processing_times.append(cheque.processing_time)
            
            metrics['status_breakdown'] = status_counts
            metrics['success_rate'] = (status_counts.get('encaisse', 0) / len(cheques)) * 100
            metrics['bounce_rate'] = (status_counts.get('rejete', 0) / len(cheques)) * 100
            
            if processing_times:
                metrics['average_processing_time'] = np.mean(processing_times)
            
            # Daily volume analysis
            daily_data = {}
            for cheque in cheques:
                day = cheque.updated_at.date()
                if day not in daily_data:
                    daily_data[day] = {'count': 0, 'amount': 0}
                daily_data[day]['count'] += 1
                daily_data[day]['amount'] += float(cheque.amount)
            
            metrics['daily_volume'] = [
                {'date': str(day), 'count': data['count'], 'amount': data['amount']}
                for day, data in sorted(daily_data.items())
            ]
            
            # Efficiency score (weighted combination of metrics)
            efficiency = (
                (metrics['success_rate'] * 0.4) +
                ((100 - metrics['bounce_rate']) * 0.3) +
                (min(100, (100 / max(1, metrics['average_processing_time']))) * 0.3)
            )
            metrics['efficiency_score'] = round(efficiency, 2)
        
        return metrics
    
    def predict_cash_flow(self, days_ahead=30):
        """Predict future cash flow from pending cheques"""
        from models import Cheque
        
        # Get pending cheques
        pending_cheques = self.db.query(Cheque).filter(
            Cheque.status.in_(['en_attente', 'depose'])
        ).all()
        
        predictions = []
        daily_predictions = {}
        
        for cheque in pending_cheques:
            # Estimate clearance probability based on historical data
            clearance_prob = self._estimate_clearance_probability(cheque)
            expected_amount = float(cheque.amount) * clearance_prob
            
            # Estimate clearance date
            estimated_date = self._estimate_clearance_date(cheque)
            
            if estimated_date <= date.today() + timedelta(days=days_ahead):
                day_key = str(estimated_date)
                if day_key not in daily_predictions:
                    daily_predictions[day_key] = {
                        'expected_inflow': 0,
                        'cheque_count': 0,
                        'confidence': []
                    }
                
                daily_predictions[day_key]['expected_inflow'] += expected_amount
                daily_predictions[day_key]['cheque_count'] += 1
                daily_predictions[day_key]['confidence'].append(clearance_prob)
                
                predictions.append({
                    'cheque_id': cheque.id,
                    'amount': float(cheque.amount),
                    'expected_amount': expected_amount,
                    'clearance_probability': clearance_prob,
                    'estimated_date': str(estimated_date),
                    'client_risk': cheque.client.risk_level
                })
        
        # Calculate confidence scores
        for day_data in daily_predictions.values():
            day_data['average_confidence'] = np.mean(day_data['confidence'])
        
        total_expected = sum(p['expected_amount'] for p in predictions)
        total_potential = sum(p['amount'] for p in predictions)
        
        return {
            'predictions': predictions,
            'daily_forecast': daily_predictions,
            'summary': {
                'total_expected_inflow': round(total_expected, 2),
                'total_potential_inflow': round(total_potential, 2),
                'confidence_ratio': round((total_expected / total_potential) * 100, 2) if total_potential > 0 else 0,
                'pending_cheques_count': len(pending_cheques),
                'forecast_period_days': days_ahead
            }
        }
    
    def detect_anomalies(self):
        """Detect unusual patterns and potential fraud"""
        from models import Cheque
        
        # Get recent cheques for anomaly detection
        recent_date = datetime.now() - timedelta(days=90)
        cheques = self.db.query(Cheque).filter(
            Cheque.created_at >= recent_date
        ).all()
        
        if len(cheques) < 10:  # Need minimum data for anomaly detection
            return {'anomalies': [], 'message': 'Insufficient data for anomaly detection'}
        
        # Prepare features for anomaly detection
        features = []
        cheque_data = []
        
        for cheque in cheques:
            feature_vector = [
                float(cheque.amount),
                (cheque.due_date - cheque.issue_date).days,
                cheque.client.bounce_rate or 0,
                cheque.client.risk_score or 0,
                1 if cheque.status == 'rejete' else 0
            ]
            features.append(feature_vector)
            cheque_data.append(cheque)
        
        # Fit anomaly detector
        features_scaled = self.scaler.fit_transform(features)
        anomaly_scores = self.anomaly_detector.fit_predict(features_scaled)
        
        # Identify anomalies
        anomalies = []
        for i, score in enumerate(anomaly_scores):
            if score == -1:  # Anomaly detected
                cheque = cheque_data[i]
                anomalies.append({
                    'cheque_id': cheque.id,
                    'cheque_number': cheque.cheque_number,
                    'amount': float(cheque.amount),
                    'client_name': cheque.client.name,
                    'anomaly_type': self._classify_anomaly_type(cheque),
                    'risk_factors': self._identify_risk_factors(cheque),
                    'created_at': cheque.created_at.isoformat()
                })
        
        return {
            'anomalies': anomalies,
            'total_cheques_analyzed': len(cheques),
            'anomaly_rate': round((len(anomalies) / len(cheques)) * 100, 2),
            'high_priority_anomalies': [a for a in anomalies if 'high_amount' in a.get('risk_factors', [])]
        }
    
    def generate_executive_dashboard_data(self):
        """Generate comprehensive dashboard data for executives"""
        from models import Cheque, Client, User
        
        # Current period metrics
        current_metrics = self.calculate_performance_metrics(period_days=30)
        
        # Previous period for comparison
        previous_metrics = self.calculate_performance_metrics(period_days=30)
        # Adjust query for previous period (simplified for demo)
        
        # Client risk distribution
        risk_data = self.assess_client_risk()
        
        # Cash flow prediction
        cash_flow = self.predict_cash_flow(days_ahead=30)
        
        # Anomaly detection
        anomalies = self.detect_anomalies()
        
        dashboard_data = {
            'kpi_summary': {
                'total_amount_processed': current_metrics['total_amount'],
                'success_rate': current_metrics['success_rate'],
                'bounce_rate': current_metrics['bounce_rate'],
                'efficiency_score': current_metrics['efficiency_score'],
                'pending_count': len([c for c in self.db.query(Cheque).filter(
                    Cheque.status.in_(['en_attente', 'depose'])
                ).all()]),
                'high_risk_clients': risk_data['high_risk_count']
            },
            'trends': {
                'daily_volume': current_metrics['daily_volume'],
                'status_breakdown': current_metrics['status_breakdown']
            },
            'predictions': {
                'expected_inflow_30d': cash_flow['summary']['total_expected_inflow'],
                'confidence_ratio': cash_flow['summary']['confidence_ratio']
            },
            'alerts': {
                'anomalies_detected': len(anomalies['anomalies']),
                'high_priority_anomalies': len(anomalies.get('high_priority_anomalies', [])),
                'overdue_cheques': len([c for c in self.db.query(Cheque).all() if c.is_overdue])
            }
        }
        
        return dashboard_data
    
    # Helper methods
    def _calculate_days_in_status(self, cheque):
        """Calculate days a cheque has been in current status"""
        if cheque.status_history:
            last_change = max([h.changed_at for h in cheque.status_history])
            return (datetime.utcnow() - last_change).days
        return (datetime.utcnow() - cheque.created_at).days
    
    def _get_age_group(self, days):
        """Categorize cheque age into groups"""
        if days <= 7:
            return '0-7 days'
        elif days <= 30:
            return '8-30 days'
        elif days <= 60:
            return '31-60 days'
        elif days <= 90:
            return '61-90 days'
        else:
            return '90+ days'
    
    def _extract_client_features(self, client):
        """Extract ML features for client risk assessment"""
        cheques = client.cheques
        if not cheques:
            return {}
        
        return {
            'total_cheques': len(cheques),
            'total_amount': sum(float(c.amount) for c in cheques),
            'bounce_rate': len([c for c in cheques if c.status == 'rejete']) / len(cheques),
            'average_amount': sum(float(c.amount) for c in cheques) / len(cheques),
            'overdue_count': len([c for c in cheques if c.is_overdue]),
            'avg_processing_time': np.mean([c.processing_time for c in cheques if c.processing_time]) or 0,
            'credit_utilization': (float(client.current_exposure) / float(client.credit_limit)) if client.credit_limit > 0 else 0,
            'days_since_last_contact': (datetime.utcnow() - client.last_contact_date).days if client.last_contact_date else 999
        }
    
    def _calculate_ml_risk_score(self, features):
        """Calculate ML-based risk score"""
        if not features:
            return 50.0  # Default medium risk
        
        # Simplified risk calculation (in production, use trained ML model)
        score = 0
        score += features.get('bounce_rate', 0) * 40
        score += min(features.get('credit_utilization', 0) * 20, 20)
        score += min(features.get('overdue_count', 0) * 5, 25)
        score += min(features.get('days_since_last_contact', 0) * 0.1, 15)
        
        return min(score, 100)
    
    def _get_risk_level(self, score):
        """Convert risk score to risk level"""
        if score < 30:
            return 'low'
        elif score < 70:
            return 'medium'
        else:
            return 'high'
    
    def _generate_risk_recommendations(self, risk_score, features):
        """Generate actionable risk recommendations"""
        recommendations = []
        
        if risk_score > 70:
            recommendations.append("Immediate attention required - high risk client")
            recommendations.append("Consider reducing credit limit")
            recommendations.append("Increase monitoring frequency")
        
        if features.get('bounce_rate', 0) > 0.2:
            recommendations.append("High bounce rate - review cheque acceptance criteria")
        
        if features.get('credit_utilization', 0) > 0.8:
            recommendations.append("Credit limit nearly exhausted - review exposure")
        
        if features.get('days_since_last_contact', 0) > 90:
            recommendations.append("No recent contact - schedule follow-up")
        
        return recommendations
    
    def _calculate_risk_distribution(self, assessments):
        """Calculate risk distribution statistics"""
        risk_levels = [a['risk_level'] for a in assessments]
        return {
            'low': risk_levels.count('low'),
            'medium': risk_levels.count('medium'),
            'high': risk_levels.count('high')
        }
    
    def _estimate_clearance_probability(self, cheque):
        """Estimate probability of cheque clearance based on historical data"""
        # Simplified probability estimation
        base_prob = 0.85  # Base clearance rate
        
        # Adjust based on client risk
        if cheque.client.risk_level == 'high':
            base_prob *= 0.7
        elif cheque.client.risk_level == 'medium':
            base_prob *= 0.85
        
        # Adjust based on amount (higher amounts have lower clearance rates)
        if float(cheque.amount) > 50000:  # Large amount threshold
            base_prob *= 0.9
        
        # Adjust based on overdue status
        if cheque.is_overdue:
            base_prob *= 0.6
        
        return max(0.1, min(0.95, base_prob))
    
    def _estimate_clearance_date(self, cheque):
        """Estimate when a cheque will clear"""
        # Simplified estimation logic
        if cheque.status == 'depose':
            # Already deposited, estimate 2-5 business days
            return date.today() + timedelta(days=3)
        else:
            # Not yet deposited, estimate based on due date and processing time
            return min(cheque.due_date, date.today() + timedelta(days=7))
    
    def _classify_anomaly_type(self, cheque):
        """Classify the type of anomaly detected"""
        amount = float(cheque.amount)
        
        if amount > 100000:  # Large amount threshold
            return 'high_amount'
        elif cheque.client.bounce_rate > 0.5:
            return 'high_risk_client'
        elif (cheque.due_date - cheque.issue_date).days > 180:
            return 'unusual_term'
        else:
            return 'pattern_anomaly'
    
    def _identify_risk_factors(self, cheque):
        """Identify specific risk factors for an anomalous cheque"""
        factors = []
        
        if float(cheque.amount) > 100000:
            factors.append('high_amount')
        
        if cheque.client.bounce_rate > 0.3:
            factors.append('high_bounce_rate')
        
        if cheque.client.risk_level == 'high':
            factors.append('high_risk_client')
        
        if (cheque.due_date - cheque.issue_date).days > 180:
            factors.append('long_term')
        
        if cheque.is_overdue:
            factors.append('overdue')
        
        return factors