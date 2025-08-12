# AI/ML utilities for intelligent features
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, mean_absolute_error
from sklearn.cluster import KMeans
import joblib
import json
from datetime import datetime, timedelta
import logging

class FraudDetectionModel:
    """Machine Learning model for fraud detection"""
    
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.feature_columns = [
            'amount', 'days_to_due', 'client_risk_score', 
            'hour_of_day', 'day_of_week', 'depositor_frequency',
            'amount_percentile', 'client_avg_amount_ratio'
        ]
        self.is_trained = False
    
    def prepare_features(self, cheque):
        """Prepare features for fraud detection"""
        features = {}
        
        # Basic features
        features['amount'] = float(cheque.amount)
        features['days_to_due'] = (cheque.due_date - cheque.issue_date).days
        features['hour_of_day'] = cheque.created_at.hour
        features['day_of_week'] = cheque.created_at.weekday()
        
        # Advanced features
        features['client_risk_score'] = self._get_client_risk_score(cheque.client_id)
        features['depositor_frequency'] = self._get_depositor_frequency(cheque.depositor_id)
        features['amount_percentile'] = self._get_amount_percentile(cheque.amount)
        features['client_avg_amount_ratio'] = self._get_client_amount_ratio(cheque)
        
        return features
    
    def _get_client_risk_score(self, client_id):
        """Calculate client risk score"""
        from models import Cheque, Client
        from sqlalchemy import func
        from app import db
        
        # Get client's rejection rate
        total_cheques = db.session.query(func.count(Cheque.id)).filter_by(client_id=client_id).scalar()
        rejected_cheques = db.session.query(func.count(Cheque.id)).filter(
            Cheque.client_id == client_id,
            Cheque.status == 'REJETE'
        ).scalar()
        
        if total_cheques == 0:
            return 0.5  # Neutral for new clients
        
        return rejected_cheques / total_cheques
    
    def _get_depositor_frequency(self, depositor_id):
        """Calculate depositor frequency score"""
        from models import Cheque
        from sqlalchemy import func
        from app import db
        
        last_30_days = datetime.now() - timedelta(days=30)
        frequency = db.session.query(func.count(Cheque.id)).filter(
            Cheque.depositor_id == depositor_id,
            Cheque.created_at >= last_30_days
        ).scalar()
        
        return min(frequency / 10.0, 1.0)  # Normalize to 0-1
    
    def _get_amount_percentile(self, amount):
        """Get amount percentile compared to recent cheques"""
        from models import Cheque
        from app import db
        
        last_90_days = datetime.now() - timedelta(days=90)
        recent_amounts = [
            row[0] for row in db.session.query(Cheque.amount).filter(
                Cheque.created_at >= last_90_days
            ).all()
        ]
        
        if not recent_amounts:
            return 0.5
        
        return np.percentile(recent_amounts, amount) / 100.0
    
    def _get_client_amount_ratio(self, cheque):
        """Get ratio of current amount to client's average"""
        from models import Cheque
        from sqlalchemy import func
        from app import db
        
        avg_amount = db.session.query(func.avg(Cheque.amount)).filter_by(
            client_id=cheque.client_id
        ).scalar()
        
        if not avg_amount:
            return 1.0
        
        return float(cheque.amount) / float(avg_amount)
    
    def train_model(self):
        """Train the fraud detection model"""
        from models import Cheque
        from app import db
        
        # Get training data (last 6 months)
        six_months_ago = datetime.now() - timedelta(days=180)
        cheques = db.session.query(Cheque).filter(
            Cheque.created_at >= six_months_ago
        ).all()
        
        if len(cheques) < 100:
            logging.warning("Insufficient data for fraud detection training")
            return False
        
        # Prepare features
        features_list = []
        for cheque in cheques:
            features = self.prepare_features(cheque)
            features_list.append([features[col] for col in self.feature_columns])
        
        X = np.array(features_list)
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled)
        self.is_trained = True
        
        # Save model
        joblib.dump(self.model, 'models/fraud_detection.pkl')
        joblib.dump(self.scaler, 'models/fraud_scaler.pkl')
        
        logging.info("Fraud detection model trained successfully")
        return True
    
    def predict_fraud_probability(self, cheque):
        """Predict fraud probability for a cheque"""
        if not self.is_trained:
            if not self.train_model():
                return 0.1  # Low default risk
        
        features = self.prepare_features(cheque)
        feature_array = np.array([[features[col] for col in self.feature_columns]])
        feature_array_scaled = self.scaler.transform(feature_array)
        
        # Get anomaly score
        anomaly_score = self.model.decision_function(feature_array_scaled)[0]
        
        # Convert to probability (0-1)
        probability = max(0, min(1, (anomaly_score + 0.5) * 2))
        
        return probability

class CashFlowPredictor:
    """Predictive model for cash flow analysis"""
    
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def prepare_training_data(self):
        """Prepare historical data for training"""
        from models import Cheque
        from app import db
        
        # Get historical data
        one_year_ago = datetime.now() - timedelta(days=365)
        cheques = db.session.query(Cheque).filter(
            Cheque.created_at >= one_year_ago,
            Cheque.status.in_(['ENCAISSE', 'REJETE'])
        ).all()
        
        data = []
        for cheque in cheques:
            features = {
                'month': cheque.created_at.month,
                'day_of_month': cheque.created_at.day,
                'day_of_week': cheque.created_at.weekday(),
                'amount': float(cheque.amount),
                'days_to_due': (cheque.due_date - cheque.issue_date).days,
                'client_risk': self._get_client_historical_risk(cheque.client_id),
                'successful': 1 if cheque.status == 'ENCAISSE' else 0
            }
            data.append(features)
        
        return pd.DataFrame(data)
    
    def _get_client_historical_risk(self, client_id):
        """Get historical risk score for client"""
        # Simplified implementation
        return 0.2  # Low risk default
    
    def train_model(self):
        """Train the cash flow prediction model"""
        df = self.prepare_training_data()
        
        if len(df) < 100:
            logging.warning("Insufficient data for cash flow prediction training")
            return False
        
        # Prepare features and target
        feature_columns = ['month', 'day_of_month', 'day_of_week', 'amount', 'days_to_due', 'client_risk']
        X = df[feature_columns]
        y = df['successful']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        logging.info(f"Cash flow model accuracy: {classification_report(y_test, y_pred)}")
        
        self.is_trained = True
        
        # Save model
        joblib.dump(self.model, 'models/cashflow_prediction.pkl')
        joblib.dump(self.scaler, 'models/cashflow_scaler.pkl')
        
        return True
    
    def predict_next_30_days(self):
        """Predict cash flow for next 30 days"""
        if not self.is_trained:
            if not self.train_model():
                return []
        
        predictions = []
        
        for i in range(30):
            future_date = datetime.now() + timedelta(days=i)
            
            # Create features for prediction
            features = np.array([[
                future_date.month,
                future_date.day,
                future_date.weekday(),
                self._estimate_daily_amount(future_date),
                7,  # Average days to due
                0.2  # Average client risk
            ]])
            
            features_scaled = self.scaler.transform(features)
            success_probability = self.model.predict_proba(features_scaled)[0][1]
            
            estimated_amount = self._estimate_daily_amount(future_date)
            predicted_amount = estimated_amount * success_probability
            
            predictions.append({
                'date': future_date.strftime('%Y-%m-%d'),
                'predicted_amount': round(predicted_amount, 2),
                'success_probability': round(success_probability, 3),
                'confidence_interval': self._calculate_confidence_interval(predicted_amount)
            })
        
        return predictions
    
    def _estimate_daily_amount(self, date):
        """Estimate daily amount based on historical patterns"""
        from models import Cheque
        from sqlalchemy import func, extract
        from app import db
        
        # Get average amount for this day of week and month
        avg_amount = db.session.query(func.avg(Cheque.amount)).filter(
            extract('month', Cheque.created_at) == date.month,
            extract('dow', Cheque.created_at) == date.weekday()
        ).scalar()
        
        return float(avg_amount or 10000)  # Default amount
    
    def _calculate_confidence_interval(self, prediction):
        """Calculate confidence interval for prediction"""
        return {
            'lower': prediction * 0.8,
            'upper': prediction * 1.2
        }

class ClientSegmentation:
    """Client segmentation using clustering"""
    
    def __init__(self):
        self.kmeans = KMeans(n_clusters=5, random_state=42)
        self.scaler = StandardScaler()
        self.segments = {
            0: 'High Value',
            1: 'Regular',
            2: 'New Client',
            3: 'Risk Client',
            4: 'Inactive'
        }
    
    def segment_clients(self):
        """Segment clients based on behavior"""
        from models import Client, Cheque
        from sqlalchemy import func
        from app import db
        
        # Get client metrics
        client_data = db.session.query(
            Client.id,
            func.count(Cheque.id).label('cheque_count'),
            func.sum(Cheque.amount).label('total_amount'),
            func.avg(Cheque.amount).label('avg_amount'),
            func.count(func.case([(Cheque.status == 'REJETE', 1)])).label('rejected_count'),
            func.max(Cheque.created_at).label('last_activity')
        ).outerjoin(Cheque).group_by(Client.id).all()
        
        if not client_data:
            return {}
        
        # Prepare features
        features = []
        client_ids = []
        
        for row in client_data:
            client_ids.append(row.id)
            
            # Calculate recency (days since last activity)
            last_activity = row.last_activity or datetime.now() - timedelta(days=365)
            recency = (datetime.now() - last_activity).days
            
            features.append([
                row.cheque_count or 0,
                float(row.total_amount or 0),
                float(row.avg_amount or 0),
                row.rejected_count or 0,
                recency
            ])
        
        # Normalize features
        features_scaled = self.scaler.fit_transform(features)
        
        # Perform clustering
        cluster_labels = self.kmeans.fit_predict(features_scaled)
        
        # Map clients to segments
        client_segments = {}
        for client_id, cluster in zip(client_ids, cluster_labels):
            client_segments[client_id] = {
                'segment_id': cluster,
                'segment_name': self.segments.get(cluster, 'Unknown'),
                'characteristics': self._get_segment_characteristics(cluster)
            }
        
        return client_segments
    
    def _get_segment_characteristics(self, cluster_id):
        """Get characteristics for each segment"""
        characteristics = {
            0: {'desc': 'High-value clients with frequent transactions'},
            1: {'desc': 'Regular clients with consistent activity'},
            2: {'desc': 'New clients with limited history'},
            3: {'desc': 'Clients with higher rejection rates'},
            4: {'desc': 'Inactive clients with recent low activity'}
        }
        return characteristics.get(cluster_id, {'desc': 'Unknown segment'})

class IntelligentRecommendations:
    """AI-powered recommendation system"""
    
    @staticmethod
    def suggest_optimal_deposit_timing(cheque):
        """Suggest optimal timing for cheque deposit"""
        from models import Cheque
        from sqlalchemy import func, extract
        from app import db
        
        # Analyze historical success rates by day of week
        success_rates = db.session.query(
            extract('dow', Cheque.created_at).label('day_of_week'),
            func.avg(func.case([(Cheque.status == 'ENCAISSE', 1)], else_=0)).label('success_rate')
        ).filter(
            Cheque.client_id == cheque.client_id
        ).group_by(extract('dow', Cheque.created_at)).all()
        
        if not success_rates:
            return {
                'recommended_day': 'Tuesday',
                'success_probability': 0.85,
                'reasoning': 'Based on general banking patterns'
            }
        
        # Find best day
        best_day = max(success_rates, key=lambda x: x.success_rate)
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        return {
            'recommended_day': days[int(best_day.day_of_week)],
            'success_probability': float(best_day.success_rate),
            'reasoning': f'Ce client a un taux de succès de {best_day.success_rate:.1%} les {days[int(best_day.day_of_week)]}'
        }
    
    @staticmethod
    def recommend_client_actions(client):
        """Recommend actions for specific client"""
        recommendations = []
        
        # Calculate client metrics
        risk_score = IntelligentRecommendations._calculate_client_risk(client)
        activity_score = IntelligentRecommendations._calculate_activity_score(client)
        
        # Risk-based recommendations
        if risk_score > 0.7:
            recommendations.append({
                'type': 'risk_mitigation',
                'action': 'Demander garantie supplémentaire',
                'priority': 'high',
                'reason': f'Score de risque élevé: {risk_score:.1%}'
            })
        
        # Activity-based recommendations
        if activity_score > 0.8:
            recommendations.append({
                'type': 'business_opportunity',
                'action': 'Proposer services premium',
                'priority': 'medium',
                'reason': 'Client très actif avec potentiel de croissance'
            })
        elif activity_score < 0.3:
            recommendations.append({
                'type': 'retention',
                'action': 'Campagne de réactivation',
                'priority': 'medium',
                'reason': 'Activité en baisse, risque de perte'
            })
        
        return recommendations
    
    @staticmethod
    def _calculate_client_risk(client):
        """Calculate comprehensive client risk score"""
        from models import Cheque
        from sqlalchemy import func
        from app import db
        
        # Get client statistics
        stats = db.session.query(
            func.count(Cheque.id).label('total'),
            func.count(func.case([(Cheque.status == 'REJETE', 1)])).label('rejected'),
            func.avg(Cheque.amount).label('avg_amount')
        ).filter_by(client_id=client.id).first()
        
        if not stats.total:
            return 0.5  # Neutral for new clients
        
        rejection_rate = stats.rejected / stats.total
        return min(rejection_rate * 2, 1.0)  # Cap at 1.0
    
    @staticmethod
    def _calculate_activity_score(client):
        """Calculate client activity score"""
        from models import Cheque
        from sqlalchemy import func
        from app import db
        
        # Activity in last 90 days vs previous 90 days
        ninety_days_ago = datetime.now() - timedelta(days=90)
        one_eighty_days_ago = datetime.now() - timedelta(days=180)
        
        recent_activity = db.session.query(func.count(Cheque.id)).filter(
            Cheque.client_id == client.id,
            Cheque.created_at >= ninety_days_ago
        ).scalar()
        
        previous_activity = db.session.query(func.count(Cheque.id)).filter(
            Cheque.client_id == client.id,
            Cheque.created_at >= one_eighty_days_ago,
            Cheque.created_at < ninety_days_ago
        ).scalar()
        
        if previous_activity == 0:
            return 0.5  # Neutral for new activity
        
        return min(recent_activity / previous_activity, 2.0) / 2.0  # Normalize to 0-1