"""
Smart Automation System for Cheque Management
Implements AI-powered automation, duplicate detection, and workflow management
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import SequenceMatcher
import json
import re
import hashlib
from threading import Thread
import time


class SmartAutomationEngine:
    """Comprehensive automation engine with AI capabilities"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.similarity_threshold = 0.85
        
    def detect_duplicate_cheques(self, batch_size=100):
        """Advanced duplicate detection using ML algorithms"""
        from models import Cheque
        
        # Get recent cheques for analysis
        recent_cheques = self.db.query(Cheque).filter(
            Cheque.created_at >= datetime.now() - timedelta(days=365)
        ).limit(batch_size * 10).all()
        
        if len(recent_cheques) < 2:
            return {'duplicates': [], 'message': 'Insufficient data for duplicate detection'}
        
        duplicates = []
        processed_pairs = set()
        
        for i, cheque1 in enumerate(recent_cheques):
            for j, cheque2 in enumerate(recent_cheques[i+1:], i+1):
                pair_key = tuple(sorted([cheque1.id, cheque2.id]))
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)
                
                similarity_score = self._calculate_cheque_similarity(cheque1, cheque2)
                
                if similarity_score >= self.similarity_threshold:
                    duplicates.append({
                        'cheque1_id': cheque1.id,
                        'cheque2_id': cheque2.id,
                        'cheque1_number': cheque1.cheque_number,
                        'cheque2_number': cheque2.cheque_number,
                        'similarity_score': round(similarity_score, 3),
                        'matching_fields': self._identify_matching_fields(cheque1, cheque2),
                        'client1': cheque1.client.name,
                        'client2': cheque2.client.name,
                        'amount1': float(cheque1.amount),
                        'amount2': float(cheque2.amount),
                        'confidence': self._calculate_duplicate_confidence(cheque1, cheque2, similarity_score)
                    })
                    
                    # Update cheques with duplicate flag
                    cheque1.duplicate_detected = True
                    cheque1.duplicate_score = similarity_score
                    cheque2.duplicate_detected = True
                    cheque2.duplicate_score = similarity_score
        
        self.db.commit()
        
        return {
            'duplicates': duplicates,
            'total_analyzed': len(recent_cheques),
            'duplicate_pairs_found': len(duplicates),
            'high_confidence_duplicates': [d for d in duplicates if d['confidence'] > 0.9]
        }
    
    def auto_assign_cheques(self, assignment_strategy='balanced'):
        """Automatically assign cheques to users based on workload and expertise"""
        from models import Cheque, User
        
        # Get unassigned cheques
        unassigned_cheques = self.db.query(Cheque).filter(
            Cheque.assigned_user_id.is_(None),
            Cheque.status.in_(['en_attente', 'depose'])
        ).all()
        
        # Get available users
        available_users = self.db.query(User).filter(
            User.is_active == True,
            User.role.in_(['manager', 'employee'])
        ).all()
        
        if not available_users or not unassigned_cheques:
            return {'assigned': 0, 'message': 'No assignments made'}
        
        assignments = []
        
        for cheque in unassigned_cheques:
            best_user = self._select_best_user_for_cheque(
                cheque, available_users, assignment_strategy
            )
            
            if best_user:
                cheque.assigned_user_id = best_user.id
                assignments.append({
                    'cheque_id': cheque.id,
                    'assigned_to': best_user.username,
                    'assignment_reason': self._get_assignment_reason(cheque, best_user)
                })
        
        self.db.commit()
        
        return {
            'assignments': assignments,
            'total_assigned': len(assignments),
            'unassigned_remaining': len(unassigned_cheques) - len(assignments)
        }
    
    def auto_prioritize_cheques(self):
        """Automatically prioritize cheques based on risk factors"""
        from models import Cheque
        
        # Get active cheques
        active_cheques = self.db.query(Cheque).filter(
            Cheque.status.in_(['en_attente', 'depose'])
        ).all()
        
        priority_updates = []
        
        for cheque in active_cheques:
            new_priority = self._calculate_cheque_priority(cheque)
            
            if cheque.priority != new_priority:
                old_priority = cheque.priority
                cheque.priority = new_priority
                
                priority_updates.append({
                    'cheque_id': cheque.id,
                    'old_priority': old_priority,
                    'new_priority': new_priority,
                    'priority_factors': self._get_priority_factors(cheque)
                })
        
        self.db.commit()
        
        return {
            'updates': priority_updates,
            'total_updated': len(priority_updates),
            'priority_distribution': self._get_priority_distribution(active_cheques)
        }
    
    def auto_send_reminders(self, test_mode=False):
        """Send automated reminders to clients and staff"""
        from models import Cheque, Client, User, ClientCommunication
        from utils.notifications import NotificationService
        
        notification_service = NotificationService(self.db)
        reminders_sent = []
        
        # Client payment reminders (3 days before due date)
        upcoming_due = self.db.query(Cheque).filter(
            and_(
                Cheque.status == 'en_attente',
                Cheque.due_date == datetime.now().date() + timedelta(days=3)
            )
        ).all()
        
        for cheque in upcoming_due:
            if cheque.client.phone or cheque.client.email:
                reminder_sent = notification_service.send_payment_reminder(
                    cheque, test_mode=test_mode
                )
                if reminder_sent:
                    reminders_sent.append({
                        'type': 'payment_reminder',
                        'cheque_id': cheque.id,
                        'client_id': cheque.client.id,
                        'method': 'sms' if cheque.client.phone else 'email'
                    })
        
        # Overdue notifications
        overdue_cheques = self.db.query(Cheque).filter(
            and_(
                Cheque.status.in_(['en_attente', 'depose']),
                Cheque.due_date < datetime.now().date()
            )
        ).all()
        
        for cheque in overdue_cheques:
            if cheque.assigned_user_id:
                notification_service.send_overdue_notification(
                    cheque, test_mode=test_mode
                )
                reminders_sent.append({
                    'type': 'overdue_notification',
                    'cheque_id': cheque.id,
                    'user_id': cheque.assigned_user_id
                })
        
        return {
            'reminders_sent': reminders_sent,
            'total_sent': len(reminders_sent),
            'payment_reminders': len([r for r in reminders_sent if r['type'] == 'payment_reminder']),
            'overdue_notifications': len([r for r in reminders_sent if r['type'] == 'overdue_notification'])
        }
    
    def auto_calculate_penalties(self):
        """Automatically calculate and apply penalties for overdue cheques"""
        from models import Cheque
        
        overdue_cheques = self.db.query(Cheque).filter(
            and_(
                Cheque.status.in_(['en_attente', 'depose']),
                Cheque.due_date < datetime.now().date(),
                or_(Cheque.penalty_amount.is_(None), Cheque.penalty_amount == 0)
            )
        ).all()
        
        penalties_applied = []
        
        for cheque in overdue_cheques:
            days_overdue = (datetime.now().date() - cheque.due_date).days
            penalty_amount = self._calculate_penalty_amount(cheque, days_overdue)
            
            if penalty_amount > 0:
                cheque.penalty_amount = penalty_amount
                penalties_applied.append({
                    'cheque_id': cheque.id,
                    'days_overdue': days_overdue,
                    'penalty_amount': float(penalty_amount),
                    'original_amount': float(cheque.amount)
                })
        
        self.db.commit()
        
        return {
            'penalties_applied': penalties_applied,
            'total_penalties': len(penalties_applied),
            'total_penalty_amount': sum(p['penalty_amount'] for p in penalties_applied)
        }
    
    def auto_risk_assessment_update(self):
        """Automatically update client risk assessments"""
        from models import Client
        from utils.advanced_analytics import AdvancedAnalyticsEngine
        
        analytics = AdvancedAnalyticsEngine(self.db)
        
        # Get clients that need risk assessment update
        update_threshold = datetime.now() - timedelta(days=30)
        clients_to_update = self.db.query(Client).filter(
            or_(
                Client.last_risk_assessment.is_(None),
                Client.last_risk_assessment < update_threshold
            )
        ).all()
        
        updates = []
        
        for client in clients_to_update:
            old_risk_level = client.risk_level
            old_risk_score = client.risk_score
            
            # Recalculate risk score
            new_risk_score = client.calculate_risk_score()
            
            if old_risk_level != client.risk_level or abs(old_risk_score - new_risk_score) > 5:
                updates.append({
                    'client_id': client.id,
                    'client_name': client.name,
                    'old_risk_level': old_risk_level,
                    'new_risk_level': client.risk_level,
                    'old_risk_score': old_risk_score,
                    'new_risk_score': new_risk_score,
                    'score_change': new_risk_score - old_risk_score
                })
        
        self.db.commit()
        
        return {
            'updates': updates,
            'total_updated': len(updates),
            'clients_assessed': len(clients_to_update),
            'high_risk_increases': len([u for u in updates if u['score_change'] > 10])
        }
    
    def schedule_automated_tasks(self):
        """Schedule and execute automated tasks"""
        scheduled_tasks = [
            {'name': 'duplicate_detection', 'frequency': 'daily', 'last_run': None},
            {'name': 'auto_assignment', 'frequency': 'hourly', 'last_run': None},
            {'name': 'priority_update', 'frequency': 'daily', 'last_run': None},
            {'name': 'send_reminders', 'frequency': 'daily', 'last_run': None},
            {'name': 'penalty_calculation', 'frequency': 'daily', 'last_run': None},
            {'name': 'risk_assessment', 'frequency': 'weekly', 'last_run': None}
        ]
        
        results = {}
        
        for task in scheduled_tasks:
            if self._should_run_task(task):
                try:
                    if task['name'] == 'duplicate_detection':
                        results[task['name']] = self.detect_duplicate_cheques()
                    elif task['name'] == 'auto_assignment':
                        results[task['name']] = self.auto_assign_cheques()
                    elif task['name'] == 'priority_update':
                        results[task['name']] = self.auto_prioritize_cheques()
                    elif task['name'] == 'send_reminders':
                        results[task['name']] = self.auto_send_reminders()
                    elif task['name'] == 'penalty_calculation':
                        results[task['name']] = self.auto_calculate_penalties()
                    elif task['name'] == 'risk_assessment':
                        results[task['name']] = self.auto_risk_assessment_update()
                    
                    task['last_run'] = datetime.now()
                    results[task['name']]['status'] = 'success'
                    
                except Exception as e:
                    results[task['name']] = {
                        'status': 'error',
                        'error': str(e)
                    }
        
        return {
            'scheduled_tasks': scheduled_tasks,
            'execution_results': results,
            'tasks_executed': len([t for t in results.values() if t.get('status') == 'success'])
        }
    
    # Helper methods
    def _calculate_cheque_similarity(self, cheque1, cheque2):
        """Calculate similarity score between two cheques"""
        similarity_factors = []
        
        # Amount similarity (exact match gets high score)
        if cheque1.amount == cheque2.amount:
            similarity_factors.append(1.0)
        else:
            amount_diff = abs(float(cheque1.amount) - float(cheque2.amount))
            max_amount = max(float(cheque1.amount), float(cheque2.amount))
            amount_similarity = max(0, 1 - (amount_diff / max_amount))
            similarity_factors.append(amount_similarity * 0.8)
        
        # Client similarity
        if cheque1.client_id == cheque2.client_id:
            similarity_factors.append(1.0)
        else:
            client_name_similarity = SequenceMatcher(
                None, cheque1.client.name.lower(), cheque2.client.name.lower()
            ).ratio()
            similarity_factors.append(client_name_similarity * 0.6)
        
        # Date similarity
        date_diff = abs((cheque1.issue_date - cheque2.issue_date).days)
        date_similarity = max(0, 1 - (date_diff / 30))  # 30 days max difference
        similarity_factors.append(date_similarity * 0.5)
        
        # Cheque number similarity
        if cheque1.cheque_number and cheque2.cheque_number:
            number_similarity = SequenceMatcher(
                None, cheque1.cheque_number, cheque2.cheque_number
            ).ratio()
            similarity_factors.append(number_similarity * 0.7)
        
        # Bank/branch similarity
        if cheque1.branch_id == cheque2.branch_id:
            similarity_factors.append(0.8)
        
        return sum(similarity_factors) / len(similarity_factors) if similarity_factors else 0
    
    def _identify_matching_fields(self, cheque1, cheque2):
        """Identify which fields match between two cheques"""
        matching_fields = []
        
        if cheque1.amount == cheque2.amount:
            matching_fields.append('amount')
        if cheque1.client_id == cheque2.client_id:
            matching_fields.append('client')
        if cheque1.branch_id == cheque2.branch_id:
            matching_fields.append('branch')
        if cheque1.cheque_number == cheque2.cheque_number:
            matching_fields.append('cheque_number')
        if abs((cheque1.issue_date - cheque2.issue_date).days) <= 1:
            matching_fields.append('issue_date')
        
        return matching_fields
    
    def _calculate_duplicate_confidence(self, cheque1, cheque2, similarity_score):
        """Calculate confidence level for duplicate detection"""
        confidence = similarity_score
        
        # Boost confidence for exact matches
        if cheque1.amount == cheque2.amount and cheque1.client_id == cheque2.client_id:
            confidence = min(1.0, confidence + 0.1)
        
        # Reduce confidence for different banks
        if cheque1.branch_id != cheque2.branch_id:
            confidence *= 0.9
        
        return round(confidence, 3)
    
    def _select_best_user_for_cheque(self, cheque, available_users, strategy='balanced'):
        """Select the best user to assign a cheque to"""
        if not available_users:
            return None
        
        if strategy == 'balanced':
            # Balance workload across users
            user_workloads = {}
            for user in available_users:
                workload = len([c for c in user.assigned_cheques if c.status in ['en_attente', 'depose']])
                user_workloads[user] = workload
            
            return min(user_workloads.keys(), key=user_workloads.get)
        
        elif strategy == 'expertise':
            # Assign based on user expertise (simplified)
            if float(cheque.amount) > 50000:  # High-value cheques to managers
                managers = [u for u in available_users if u.role == 'manager']
                return managers[0] if managers else available_users[0]
        
        return available_users[0]  # Default assignment
    
    def _get_assignment_reason(self, cheque, user):
        """Get reason for assignment"""
        if user.role == 'manager' and float(cheque.amount) > 50000:
            return 'High value cheque assigned to manager'
        elif cheque.client.risk_level == 'high':
            return 'High risk client requires experienced handler'
        else:
            return 'Balanced workload distribution'
    
    def _calculate_cheque_priority(self, cheque):
        """Calculate priority level for a cheque"""
        priority_score = 0
        
        # Amount factor
        if float(cheque.amount) > 100000:
            priority_score += 3
        elif float(cheque.amount) > 50000:
            priority_score += 2
        elif float(cheque.amount) > 10000:
            priority_score += 1
        
        # Due date factor
        days_to_due = (cheque.due_date - datetime.now().date()).days
        if days_to_due < 0:  # Overdue
            priority_score += 4
        elif days_to_due <= 3:
            priority_score += 3
        elif days_to_due <= 7:
            priority_score += 2
        
        # Client risk factor
        if cheque.client.risk_level == 'high':
            priority_score += 2
        elif cheque.client.risk_level == 'medium':
            priority_score += 1
        
        # Convert score to priority level
        if priority_score >= 6:
            return 'urgent'
        elif priority_score >= 4:
            return 'high'
        elif priority_score >= 2:
            return 'normal'
        else:
            return 'low'
    
    def _get_priority_factors(self, cheque):
        """Get factors that influenced priority calculation"""
        factors = []
        
        if float(cheque.amount) > 50000:
            factors.append('high_amount')
        if cheque.is_overdue:
            factors.append('overdue')
        elif (cheque.due_date - datetime.now().date()).days <= 3:
            factors.append('due_soon')
        if cheque.client.risk_level == 'high':
            factors.append('high_risk_client')
        
        return factors
    
    def _get_priority_distribution(self, cheques):
        """Get distribution of priorities"""
        priorities = [c.priority for c in cheques]
        return {
            'urgent': priorities.count('urgent'),
            'high': priorities.count('high'),
            'normal': priorities.count('normal'),
            'low': priorities.count('low')
        }
    
    def _calculate_penalty_amount(self, cheque, days_overdue):
        """Calculate penalty amount for overdue cheque"""
        base_amount = float(cheque.amount)
        daily_penalty_rate = 0.001  # 0.1% per day
        
        # Progressive penalty rates
        if days_overdue <= 30:
            penalty_rate = daily_penalty_rate
        elif days_overdue <= 60:
            penalty_rate = daily_penalty_rate * 1.5
        else:
            penalty_rate = daily_penalty_rate * 2
        
        penalty = base_amount * penalty_rate * days_overdue
        return min(penalty, base_amount * 0.1)  # Cap at 10% of original amount
    
    def _should_run_task(self, task):
        """Determine if a scheduled task should run"""
        if not task['last_run']:
            return True
        
        now = datetime.now()
        time_diff = now - task['last_run']
        
        if task['frequency'] == 'hourly':
            return time_diff.total_seconds() >= 3600
        elif task['frequency'] == 'daily':
            return time_diff.days >= 1
        elif task['frequency'] == 'weekly':
            return time_diff.days >= 7
        
        return False


class WorkflowManager:
    """Manage custom workflow chains and business rules"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.workflow_rules = self._load_workflow_rules()
    
    def execute_workflow(self, cheque_id, action):
        """Execute workflow action on a cheque"""
        from models import Cheque, ChequeStatusHistory
        
        cheque = self.db.query(Cheque).get(cheque_id)
        if not cheque:
            return {'error': 'Cheque not found'}
        
        # Check if action is allowed for current status
        allowed_actions = self.workflow_rules.get(cheque.status, [])
        if action not in allowed_actions:
            return {'error': f'Action {action} not allowed for status {cheque.status}'}
        
        # Execute the action
        old_status = cheque.status
        new_status = self._get_new_status(action)
        
        if new_status:
            # Update cheque status
            cheque.status = new_status
            
            # Record status history
            history = ChequeStatusHistory(
                cheque_id=cheque.id,
                old_status=old_status,
                new_status=new_status,
                changed_at=datetime.now()
            )
            self.db.add(history)
            
            # Execute post-action hooks
            self._execute_post_action_hooks(cheque, action, old_status, new_status)
            
            self.db.commit()
            
            return {
                'success': True,
                'old_status': old_status,
                'new_status': new_status,
                'cheque_id': cheque_id
            }
        
        return {'error': 'Invalid action'}
    
    def _load_workflow_rules(self):
        """Load workflow rules configuration"""
        return {
            'en_attente': ['deposit', 'reject', 'cancel'],
            'depose': ['clear', 'bounce', 'cancel'],
            'encaisse': ['reverse'],
            'rejete': ['reprocess', 'cancel'],
            'impaye': ['reprocess', 'cancel'],
            'annule': []
        }
    
    def _get_new_status(self, action):
        """Map action to new status"""
        action_map = {
            'deposit': 'depose',
            'clear': 'encaisse',
            'bounce': 'rejete',
            'reject': 'rejete',
            'cancel': 'annule',
            'reprocess': 'en_attente',
            'reverse': 'impaye'
        }
        return action_map.get(action)
    
    def _execute_post_action_hooks(self, cheque, action, old_status, new_status):
        """Execute post-action business logic"""
        # Update client exposure
        if new_status == 'encaisse':
            cheque.client.current_exposure -= float(cheque.amount)
        elif old_status == 'encaisse' and new_status in ['rejete', 'impaye']:
            cheque.client.current_exposure += float(cheque.amount)
        
        # Update bounce rate if cheque bounced
        if new_status == 'rejete':
            total_cheques = len(cheque.client.cheques)
            bounced_cheques = len([c for c in cheque.client.cheques if c.status == 'rejete'])
            cheque.client.bounce_rate = bounced_cheques / total_cheques if total_cheques > 0 else 0
        
        # Set processing dates
        if new_status == 'depose':
            cheque.deposit_date = datetime.now().date()
        elif new_status == 'encaisse':
            cheque.clearance_date = datetime.now().date()
        elif new_status == 'rejete':
            cheque.rejection_date = datetime.now().date()