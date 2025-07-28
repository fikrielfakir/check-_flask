"""
Advanced Analytics Engine for Cheque Management System
Implements comprehensive analytics, reporting, and predictive features.
"""

import os
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict, Counter
import json
import sqlite3
from dataclasses import dataclass
from enum import Enum

# Analytics Models
@dataclass
class ChequeAgingReport:
    """Cheque aging analysis data structure"""
    status: str
    avg_days: float
    min_days: int
    max_days: int
    total_cheques: int
    total_amount: float
    percentage: float

@dataclass
class SeasonalTrend:
    """Seasonal trend analysis data structure"""
    period: str
    inflow_count: int
    inflow_amount: float
    outflow_count: int
    outflow_amount: float
    net_amount: float
    trend_direction: str

@dataclass
class ClientRiskProfile:
    """Client risk assessment data structure"""
    client_id: int
    client_name: str
    total_cheques: int
    bounced_cheques: int
    bounce_rate: float
    avg_amount: float
    risk_level: str
    risk_score: int
    last_bounce_date: Optional[date]

@dataclass
class PerformanceMetrics:
    """System performance metrics"""
    avg_processing_time: float
    success_rate: float
    total_processed: int
    on_time_rate: float
    efficiency_score: float

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AnalyticsEngine:
    """Comprehensive analytics engine for cheque management"""
    
    def __init__(self, db_path: str):
        """Initialize analytics engine with database connection"""
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
    def get_db_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def calculate_cheque_aging(self, status_filter: Optional[str] = None) -> List[ChequeAgingReport]:
        """
        Calculate aging analysis for cheques by status
        
        Args:
            status_filter: Optional status to filter by
            
        Returns:
            List of ChequeAgingReport objects
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Base query for aging analysis
            base_query = """
                SELECT 
                    status,
                    AVG(JULIANDAY('now') - JULIANDAY(issue_date)) as avg_days,
                    MIN(JULIANDAY('now') - JULIANDAY(issue_date)) as min_days,
                    MAX(JULIANDAY('now') - JULIANDAY(issue_date)) as max_days,
                    COUNT(*) as total_cheques,
                    SUM(amount) as total_amount
                FROM cheques 
                WHERE issue_date IS NOT NULL
            """
            
            if status_filter:
                base_query += f" AND status = '{status_filter}'"
            
            base_query += " GROUP BY status ORDER BY avg_days DESC"
            
            cursor.execute(base_query)
            results = cursor.fetchall()
            
            # Calculate total for percentages
            total_cheques = sum(row['total_cheques'] for row in results)
            
            aging_reports = []
            for row in results:
                percentage = (row['total_cheques'] / total_cheques * 100) if total_cheques > 0 else 0
                
                aging_reports.append(ChequeAgingReport(
                    status=row['status'],
                    avg_days=round(row['avg_days'], 1),
                    min_days=int(row['min_days']),
                    max_days=int(row['max_days']),
                    total_cheques=row['total_cheques'],
                    total_amount=float(row['total_amount']),
                    percentage=round(percentage, 2)
                ))
            
            conn.close()
            return aging_reports
            
        except Exception as e:
            self.logger.error(f"Error calculating cheque aging: {str(e)}")
            return []
    
    def analyze_seasonal_trends(self, months_back: int = 12) -> List[SeasonalTrend]:
        """
        Analyze seasonal trends for cheque inflow/outflow
        
        Args:
            months_back: Number of months to analyze
            
        Returns:
            List of SeasonalTrend objects
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months_back * 30)
            
            query = """
                SELECT 
                    strftime('%Y-%m', issue_date) as period,
                    COUNT(CASE WHEN status IN ('ENCAISSE', 'DEPOSE') THEN 1 END) as inflow_count,
                    SUM(CASE WHEN status IN ('ENCAISSE', 'DEPOSE') THEN amount ELSE 0 END) as inflow_amount,
                    COUNT(CASE WHEN status IN ('REJETE', 'IMPAYE', 'ANNULE') THEN 1 END) as outflow_count,
                    SUM(CASE WHEN status IN ('REJETE', 'IMPAYE', 'ANNULE') THEN amount ELSE 0 END) as outflow_amount
                FROM cheques 
                WHERE issue_date >= ? AND issue_date <= ?
                GROUP BY strftime('%Y-%m', issue_date)
                ORDER BY period DESC
            """
            
            cursor.execute(query, (start_date.date(), end_date.date()))
            results = cursor.fetchall()
            
            trends = []
            prev_net = None
            
            for row in results:
                inflow_amount = float(row['inflow_amount'] or 0)
                outflow_amount = float(row['outflow_amount'] or 0)
                net_amount = inflow_amount - outflow_amount
                
                # Determine trend direction
                if prev_net is None:
                    trend_direction = "stable"
                elif net_amount > prev_net:
                    trend_direction = "up"
                elif net_amount < prev_net:
                    trend_direction = "down"
                else:
                    trend_direction = "stable"
                
                trends.append(SeasonalTrend(
                    period=row['period'],
                    inflow_count=row['inflow_count'],
                    inflow_amount=inflow_amount,
                    outflow_count=row['outflow_count'],
                    outflow_amount=outflow_amount,
                    net_amount=net_amount,
                    trend_direction=trend_direction
                ))
                
                prev_net = net_amount
            
            conn.close()
            return trends
            
        except Exception as e:
            self.logger.error(f"Error analyzing seasonal trends: {str(e)}")
            return []
    
    def assess_client_risk(self, min_cheques: int = 5) -> List[ClientRiskProfile]:
        """
        Assess client risk based on bounce rates and patterns
        
        Args:
            min_cheques: Minimum number of cheques for risk assessment
            
        Returns:
            List of ClientRiskProfile objects
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    c.client_id,
                    cl.name as client_name,
                    COUNT(*) as total_cheques,
                    COUNT(CASE WHEN c.status IN ('REJETE', 'IMPAYE') THEN 1 END) as bounced_cheques,
                    AVG(c.amount) as avg_amount,
                    MAX(CASE WHEN c.status IN ('REJETE', 'IMPAYE') THEN c.issue_date END) as last_bounce_date
                FROM cheques c
                JOIN clients cl ON c.client_id = cl.id
                GROUP BY c.client_id, cl.name
                HAVING COUNT(*) >= ?
                ORDER BY bounced_cheques DESC, total_cheques DESC
            """
            
            cursor.execute(query, (min_cheques,))
            results = cursor.fetchall()
            
            risk_profiles = []
            for row in results:
                total_cheques = row['total_cheques']
                bounced_cheques = row['bounced_cheques']
                bounce_rate = (bounced_cheques / total_cheques * 100) if total_cheques > 0 else 0
                
                # Calculate risk score (0-100)
                risk_score = min(100, int(bounce_rate * 2 + (bounced_cheques / 10) * 5))
                
                # Determine risk level
                if bounce_rate >= 20 or risk_score >= 80:
                    risk_level = RiskLevel.CRITICAL.value
                elif bounce_rate >= 10 or risk_score >= 60:
                    risk_level = RiskLevel.HIGH.value
                elif bounce_rate >= 5 or risk_score >= 30:
                    risk_level = RiskLevel.MEDIUM.value
                else:
                    risk_level = RiskLevel.LOW.value
                
                # Parse last bounce date
                last_bounce_date = None
                if row['last_bounce_date']:
                    try:
                        last_bounce_date = datetime.strptime(row['last_bounce_date'], '%Y-%m-%d').date()
                    except ValueError:
                        pass
                
                risk_profiles.append(ClientRiskProfile(
                    client_id=row['client_id'],
                    client_name=row['client_name'],
                    total_cheques=total_cheques,
                    bounced_cheques=bounced_cheques,
                    bounce_rate=round(bounce_rate, 2),
                    avg_amount=round(float(row['avg_amount']), 2),
                    risk_level=risk_level,
                    risk_score=risk_score,
                    last_bounce_date=last_bounce_date
                ))
            
            conn.close()
            return risk_profiles
            
        except Exception as e:
            self.logger.error(f"Error assessing client risk: {str(e)}")
            return []
    
    def calculate_performance_metrics(self, days_back: int = 30) -> PerformanceMetrics:
        """
        Calculate system performance metrics
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            PerformanceMetrics object
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Performance queries
            queries = {
                'processing_time': """
                    SELECT AVG(JULIANDAY(due_date) - JULIANDAY(issue_date)) as avg_processing
                    FROM cheques 
                    WHERE issue_date >= ? AND due_date IS NOT NULL
                """,
                'success_rate': """
                    SELECT 
                        COUNT(CASE WHEN status = 'ENCAISSE' THEN 1 END) as successful,
                        COUNT(*) as total
                    FROM cheques 
                    WHERE issue_date >= ?
                """,
                'on_time_rate': """
                    SELECT 
                        COUNT(CASE WHEN due_date >= issue_date THEN 1 END) as on_time,
                        COUNT(*) as total
                    FROM cheques 
                    WHERE issue_date >= ? AND due_date IS NOT NULL
                """
            }
            
            # Execute queries
            cursor.execute(queries['processing_time'], (start_date.date(),))
            processing_result = cursor.fetchone()
            avg_processing_time = float(processing_result['avg_processing'] or 0)
            
            cursor.execute(queries['success_rate'], (start_date.date(),))
            success_result = cursor.fetchone()
            total_processed = success_result['total']
            success_rate = (success_result['successful'] / total_processed * 100) if total_processed > 0 else 0
            
            cursor.execute(queries['on_time_rate'], (start_date.date(),))
            ontime_result = cursor.fetchone()
            on_time_rate = (ontime_result['on_time'] / ontime_result['total'] * 100) if ontime_result['total'] > 0 else 0
            
            # Calculate efficiency score (composite metric)
            efficiency_score = (success_rate * 0.4 + on_time_rate * 0.3 + max(0, 100 - avg_processing_time) * 0.3)
            
            conn.close()
            
            return PerformanceMetrics(
                avg_processing_time=round(avg_processing_time, 2),
                success_rate=round(success_rate, 2),
                total_processed=total_processed,
                on_time_rate=round(on_time_rate, 2),
                efficiency_score=round(efficiency_score, 2)
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {str(e)}")
            return PerformanceMetrics(0, 0, 0, 0, 0)
    
    def predict_cash_flow(self, days_ahead: int = 30) -> Dict[str, Any]:
        """
        Predict future cash flow based on pending cheques
        
        Args:
            days_ahead: Number of days to predict ahead
            
        Returns:
            Dictionary with cash flow predictions
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get pending cheques
            end_date = datetime.now() + timedelta(days=days_ahead)
            
            query = """
                SELECT 
                    due_date,
                    SUM(amount) as daily_amount,
                    COUNT(*) as daily_count
                FROM cheques 
                WHERE status = 'EN_ATTENTE' 
                    AND due_date BETWEEN date('now') AND date('now', '+{} days')
                GROUP BY due_date
                ORDER BY due_date
            """.format(days_ahead)
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Calculate predictions
            daily_predictions = []
            cumulative_amount = 0
            
            for row in results:
                daily_amount = float(row['daily_amount'])
                cumulative_amount += daily_amount
                
                daily_predictions.append({
                    'date': row['due_date'],
                    'amount': daily_amount,
                    'count': row['daily_count'],
                    'cumulative': cumulative_amount
                })
            
            # Calculate summary statistics
            total_predicted = sum(p['amount'] for p in daily_predictions)
            avg_daily = total_predicted / days_ahead if days_ahead > 0 else 0
            
            # Risk adjustment based on historical success rate
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN status = 'ENCAISSE' THEN 1 END) * 100.0 / COUNT(*) as success_rate
                FROM cheques 
                WHERE issue_date >= date('now', '-90 days')
            """)
            
            success_rate_result = cursor.fetchone()
            success_rate = float(success_rate_result['success_rate'] or 80) / 100
            
            adjusted_total = total_predicted * success_rate
            
            conn.close()
            
            return {
                'total_predicted': round(total_predicted, 2),
                'adjusted_total': round(adjusted_total, 2),
                'success_rate': round(success_rate * 100, 2),
                'avg_daily': round(avg_daily, 2),
                'daily_predictions': daily_predictions,
                'confidence_level': 'high' if success_rate > 0.8 else 'medium' if success_rate > 0.6 else 'low'
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting cash flow: {str(e)}")
            return {}
    
    def generate_kpi_dashboard(self) -> Dict[str, Any]:
        """
        Generate comprehensive KPI dashboard data
        
        Returns:
            Dictionary with all KPI metrics
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Current month metrics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_cheques,
                    SUM(amount) as total_amount,
                    COUNT(CASE WHEN status = 'ENCAISSE' THEN 1 END) as successful_cheques,
                    COUNT(CASE WHEN status = 'REJETE' THEN 1 END) as bounced_cheques,
                    COUNT(CASE WHEN status = 'EN_ATTENTE' THEN 1 END) as pending_cheques,
                    AVG(amount) as avg_amount
                FROM cheques 
                WHERE strftime('%Y-%m', issue_date) = strftime('%Y-%m', 'now')
            """)
            
            current_month = cursor.fetchone()
            
            # Previous month for comparison
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_cheques,
                    SUM(amount) as total_amount
                FROM cheques 
                WHERE strftime('%Y-%m', issue_date) = strftime('%Y-%m', 'now', '-1 month')
            """)
            
            previous_month = cursor.fetchone()
            
            # Calculate growth rates
            current_count = current_month['total_cheques']
            previous_count = previous_month['total_cheques'] or 1
            count_growth = ((current_count - previous_count) / previous_count * 100) if previous_count > 0 else 0
            
            current_amount = float(current_month['total_amount'] or 0)
            previous_amount = float(previous_month['total_amount'] or 0) or 1
            amount_growth = ((current_amount - previous_amount) / previous_amount * 100) if previous_amount > 0 else 0
            
            # Top performing clients
            cursor.execute("""
                SELECT 
                    cl.name,
                    COUNT(*) as cheque_count,
                    SUM(c.amount) as total_amount
                FROM cheques c
                JOIN clients cl ON c.client_id = cl.id
                WHERE strftime('%Y-%m', c.issue_date) = strftime('%Y-%m', 'now')
                GROUP BY cl.id, cl.name
                ORDER BY total_amount DESC
                LIMIT 5
            """)
            
            top_clients = [dict(row) for row in cursor.fetchall()]
            
            # Bank performance
            cursor.execute("""
                SELECT 
                    b.name as bank_name,
                    COUNT(*) as cheque_count,
                    SUM(c.amount) as total_amount,
                    COUNT(CASE WHEN c.status = 'ENCAISSE' THEN 1 END) * 100.0 / COUNT(*) as success_rate
                FROM cheques c
                JOIN branches br ON c.branch_id = br.id
                JOIN banks b ON br.bank_id = b.id
                WHERE strftime('%Y-%m', c.issue_date) = strftime('%Y-%m', 'now')
                GROUP BY b.id, b.name
                ORDER BY success_rate DESC
                LIMIT 5
            """)
            
            bank_performance = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'current_month': {
                    'total_cheques': current_count,
                    'total_amount': current_amount,
                    'successful_cheques': current_month['successful_cheques'],
                    'bounced_cheques': current_month['bounced_cheques'],
                    'pending_cheques': current_month['pending_cheques'],
                    'avg_amount': round(float(current_month['avg_amount'] or 0), 2),
                    'success_rate': round((current_month['successful_cheques'] / current_count * 100) if current_count > 0 else 0, 2)
                },
                'growth_metrics': {
                    'count_growth': round(count_growth, 2),
                    'amount_growth': round(amount_growth, 2)
                },
                'top_clients': top_clients,
                'bank_performance': bank_performance,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating KPI dashboard: {str(e)}")
            return {}
    
    def export_analytics_report(self, report_type: str, output_path: str) -> str:
        """
        Export comprehensive analytics report
        
        Args:
            report_type: Type of report ('aging', 'trends', 'risk', 'performance', 'complete')
            output_path: Path to save the report
            
        Returns:
            Path to the generated report file
        """
        try:
            report_data = {}
            
            if report_type in ['aging', 'complete']:
                report_data['aging_analysis'] = self.calculate_cheque_aging()
            
            if report_type in ['trends', 'complete']:
                report_data['seasonal_trends'] = self.analyze_seasonal_trends()
            
            if report_type in ['risk', 'complete']:
                report_data['client_risk'] = self.assess_client_risk()
            
            if report_type in ['performance', 'complete']:
                report_data['performance_metrics'] = self.calculate_performance_metrics()
                report_data['cash_flow_prediction'] = self.predict_cash_flow()
            
            if report_type in ['complete']:
                report_data['kpi_dashboard'] = self.generate_kpi_dashboard()
            
            # Convert dataclasses to dictionaries for JSON serialization
            def convert_dataclass(obj):
                if hasattr(obj, '__dict__'):
                    result = {}
                    for key, value in obj.__dict__.items():
                        if isinstance(value, date):
                            result[key] = value.isoformat()
                        else:
                            result[key] = value
                    return result
                return obj
            
            # Serialize data
            serialized_data = {}
            for key, value in report_data.items():
                if isinstance(value, list):
                    serialized_data[key] = [convert_dataclass(item) for item in value]
                else:
                    serialized_data[key] = convert_dataclass(value)
            
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(serialized_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Analytics report exported to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error exporting analytics report: {str(e)}")
            raise
    
    def get_duplicate_cheques(self, similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        Detect potential duplicate cheques using advanced matching
        
        Args:
            similarity_threshold: Similarity threshold for matching (0.0 to 1.0)
            
        Returns:
            List of potential duplicate groups
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get all cheques with key fields
            cursor.execute("""
                SELECT 
                    id, cheque_number, amount, issue_date, client_id, branch_id,
                    cl.name as client_name, b.name as bank_name
                FROM cheques c
                JOIN clients cl ON c.client_id = cl.id
                JOIN branches br ON c.branch_id = br.id
                JOIN banks b ON br.bank_id = b.id
                ORDER BY cheque_number, amount
            """)
            
            cheques = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            duplicates = []
            processed_ids = set()
            
            for i, cheque1 in enumerate(cheques):
                if cheque1['id'] in processed_ids:
                    continue
                
                group = [cheque1]
                
                for j, cheque2 in enumerate(cheques[i+1:], i+1):
                    if cheque2['id'] in processed_ids:
                        continue
                    
                    # Calculate similarity score
                    similarity = self._calculate_cheque_similarity(cheque1, cheque2)
                    
                    if similarity >= similarity_threshold:
                        group.append(cheque2)
                        processed_ids.add(cheque2['id'])
                
                if len(group) > 1:
                    duplicates.append({
                        'group_id': len(duplicates) + 1,
                        'cheques': group,
                        'similarity_score': similarity_threshold,
                        'potential_duplicate_count': len(group)
                    })
                    
                    for cheque in group:
                        processed_ids.add(cheque['id'])
            
            return duplicates
            
        except Exception as e:
            self.logger.error(f"Error detecting duplicate cheques: {str(e)}")
            return []
    
    def _calculate_cheque_similarity(self, cheque1: Dict, cheque2: Dict) -> float:
        """Calculate similarity score between two cheques"""
        score = 0.0
        factors = 0
        
        # Cheque number similarity (exact match)
        if cheque1['cheque_number'] and cheque2['cheque_number']:
            if cheque1['cheque_number'] == cheque2['cheque_number']:
                score += 0.4
            factors += 0.4
        
        # Amount similarity (exact match or very close)
        if cheque1['amount'] and cheque2['amount']:
            amount_diff = abs(float(cheque1['amount']) - float(cheque2['amount']))
            if amount_diff == 0:
                score += 0.3
            elif amount_diff < 1:  # Very close amounts
                score += 0.2
            factors += 0.3
        
        # Client similarity
        if cheque1['client_id'] == cheque2['client_id']:
            score += 0.2
        factors += 0.2
        
        # Bank similarity
        if cheque1['branch_id'] == cheque2['branch_id']:
            score += 0.1
        factors += 0.1
        
        return score / factors if factors > 0 else 0.0