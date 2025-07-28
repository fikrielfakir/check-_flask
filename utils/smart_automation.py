"""
Smart Automation Features for Cheque Management System
Implements automated workflows, notifications, and AI-powered features.
"""

import os
import logging
import sqlite3
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
import hashlib
import difflib
from collections import defaultdict

# Automation Models
@dataclass
class AutomationRule:
    """Automation rule configuration"""
    id: str
    name: str
    trigger_type: str
    trigger_conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    active: bool
    created_date: datetime
    last_executed: Optional[datetime]

@dataclass
class NotificationTemplate:
    """Notification template structure"""
    id: str
    name: str
    type: str  # sms, email, system
    template: str
    variables: List[str]
    active: bool

@dataclass
class DuplicateMatch:
    """Duplicate detection match result"""
    cheque1_id: int
    cheque2_id: int
    similarity_score: float
    matching_fields: List[str]
    confidence_level: str
    suggested_action: str

class SmartAutomation:
    """Smart automation engine for cheque management"""
    
    def __init__(self, db_path: str):
        """Initialize smart automation engine"""
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.setup_automation_tables()
    
    def get_db_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def setup_automation_tables(self):
        """Setup automation-related database tables"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Automation rules table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS automation_rules (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    trigger_type TEXT NOT NULL,
                    trigger_conditions TEXT NOT NULL,
                    actions TEXT NOT NULL,
                    active BOOLEAN DEFAULT 1,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_executed TIMESTAMP NULL
                )
            """)
            
            # Notification templates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notification_templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    template TEXT NOT NULL,
                    variables TEXT NOT NULL,
                    active BOOLEAN DEFAULT 1,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Automation logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS automation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT NOT NULL,
                    execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT NOT NULL,
                    details TEXT,
                    affected_records INTEGER DEFAULT 0
                )
            """)
            
            # Duplicate detection results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS duplicate_detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cheque1_id INTEGER NOT NULL,
                    cheque2_id INTEGER NOT NULL,
                    similarity_score REAL NOT NULL,
                    matching_fields TEXT NOT NULL,
                    confidence_level TEXT NOT NULL,
                    suggested_action TEXT NOT NULL,
                    detection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved BOOLEAN DEFAULT 0,
                    resolution_action TEXT NULL
                )
            """)
            
            conn.commit()
            conn.close()
            
            # Initialize default rules and templates
            self._initialize_default_automation()
            
        except Exception as e:
            self.logger.error(f"Error setting up automation tables: {str(e)}")
    
    def _initialize_default_automation(self):
        """Initialize default automation rules and templates"""
        try:
            # Default automation rules
            default_rules = [
                {
                    'id': 'due_date_reminder',
                    'name': 'Rappel échéance chèque',
                    'trigger_type': 'schedule',
                    'trigger_conditions': {'schedule': 'daily', 'time': '08:00'},
                    'actions': [
                        {'type': 'notification', 'template': 'due_reminder', 'recipients': 'assigned_users'},
                        {'type': 'status_update', 'condition': 'overdue', 'new_status': 'OVERDUE'}
                    ],
                    'active': True
                },
                {
                    'id': 'bounce_alert',
                    'name': 'Alerte chèque rejeté',
                    'trigger_type': 'status_change',
                    'trigger_conditions': {'status': 'REJETE'},
                    'actions': [
                        {'type': 'notification', 'template': 'bounce_alert', 'recipients': 'admin'},
                        {'type': 'client_risk_update', 'increment': 10}
                    ],
                    'active': True
                },
                {
                    'id': 'duplicate_detection',
                    'name': 'Détection automatique de doublons',
                    'trigger_type': 'cheque_creation',
                    'trigger_conditions': {'similarity_threshold': 0.85},
                    'actions': [
                        {'type': 'duplicate_check', 'action': 'flag_and_notify'},
                        {'type': 'notification', 'template': 'duplicate_alert', 'recipients': 'data_admin'}
                    ],
                    'active': True
                },
                {
                    'id': 'performance_optimization',
                    'name': 'Optimisation automatique des performances',
                    'trigger_type': 'schedule',
                    'trigger_conditions': {'schedule': 'weekly', 'day': 'sunday', 'time': '02:00'},
                    'actions': [
                        {'type': 'database_cleanup', 'action': 'optimize_indexes'},
                        {'type': 'cache_refresh', 'action': 'clear_old_cache'},
                        {'type': 'backup_creation', 'action': 'weekly_backup'}
                    ],
                    'active': True
                }
            ]
            
            # Default notification templates
            default_templates = [
                {
                    'id': 'due_reminder',
                    'name': 'Rappel échéance chèque',
                    'type': 'system',
                    'template': 'Le chèque #{cheque_number} de {client_name} arrive à échéance le {due_date}. Montant: {amount} MAD',
                    'variables': ['cheque_number', 'client_name', 'due_date', 'amount']
                },
                {
                    'id': 'bounce_alert',
                    'name': 'Alerte chèque rejeté',
                    'type': 'system',
                    'template': 'ALERTE: Le chèque #{cheque_number} de {client_name} a été rejeté. Montant: {amount} MAD. Raison: {reason}',
                    'variables': ['cheque_number', 'client_name', 'amount', 'reason']
                },
                {
                    'id': 'duplicate_alert',
                    'name': 'Alerte doublon détecté',
                    'type': 'system',
                    'template': 'Doublon potentiel détecté: Chèques #{cheque1_number} et #{cheque2_number}. Similarité: {similarity}%',
                    'variables': ['cheque1_number', 'cheque2_number', 'similarity']
                },
                {
                    'id': 'client_risk_alert',
                    'name': 'Alerte risque client',
                    'type': 'system',
                    'template': 'ATTENTION: Le client {client_name} présente un risque élevé. Taux de rejet: {bounce_rate}%',
                    'variables': ['client_name', 'bounce_rate']
                }
            ]
            
            # Insert default rules and templates
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            for rule in default_rules:
                cursor.execute("""
                    INSERT OR IGNORE INTO automation_rules 
                    (id, name, trigger_type, trigger_conditions, actions, active)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    rule['id'], rule['name'], rule['trigger_type'],
                    json.dumps(rule['trigger_conditions']),
                    json.dumps(rule['actions']),
                    rule['active']
                ))
            
            for template in default_templates:
                cursor.execute("""
                    INSERT OR IGNORE INTO notification_templates
                    (id, name, type, template, variables, active)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    template['id'], template['name'], template['type'],
                    template['template'], json.dumps(template['variables']), True
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error initializing default automation: {str(e)}")
    
    def detect_advanced_duplicates(self, similarity_threshold: float = 0.8) -> List[DuplicateMatch]:
        """
        Advanced duplicate detection with machine learning-like similarity
        
        Args:
            similarity_threshold: Minimum similarity score for duplicate detection
            
        Returns:
            List of DuplicateMatch objects
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get all cheques with detailed information
            cursor.execute("""
                SELECT 
                    c.id, c.cheque_number, c.amount, c.issue_date, c.due_date,
                    c.depositor_name, c.notes, c.status,
                    cl.name as client_name, cl.phone, cl.email,
                    b.name as bank_name, br.name as branch_name
                FROM cheques c
                JOIN clients cl ON c.client_id = cl.id
                JOIN branches br ON c.branch_id = br.id
                JOIN banks b ON br.bank_id = b.id
                ORDER BY c.id
            """)
            
            cheques = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            duplicates = []
            processed_pairs = set()
            
            for i, cheque1 in enumerate(cheques):
                for j, cheque2 in enumerate(cheques[i+1:], i+1):
                    pair_key = tuple(sorted([cheque1['id'], cheque2['id']]))
                    if pair_key in processed_pairs:
                        continue
                    
                    similarity_result = self._calculate_advanced_similarity(cheque1, cheque2)
                    
                    if similarity_result['score'] >= similarity_threshold:
                        duplicates.append(DuplicateMatch(
                            cheque1_id=cheque1['id'],
                            cheque2_id=cheque2['id'],
                            similarity_score=similarity_result['score'],
                            matching_fields=similarity_result['matching_fields'],
                            confidence_level=similarity_result['confidence'],
                            suggested_action=similarity_result['suggested_action']
                        ))
                        
                        processed_pairs.add(pair_key)
            
            # Save to database
            self._save_duplicate_detections(duplicates)
            
            return duplicates
            
        except Exception as e:
            self.logger.error(f"Error in advanced duplicate detection: {str(e)}")
            return []
    
    def _calculate_advanced_similarity(self, cheque1: Dict, cheque2: Dict) -> Dict[str, Any]:
        """Calculate advanced similarity between two cheques"""
        matching_fields = []
        similarity_scores = []
        weights = {
            'cheque_number': 0.3,
            'amount': 0.25,
            'client_name': 0.2,
            'bank_info': 0.1,
            'dates': 0.1,
            'additional_info': 0.05
        }
        
        # Cheque number similarity
        num_sim = self._string_similarity(str(cheque1.get('cheque_number', '')), 
                                        str(cheque2.get('cheque_number', '')))
        if num_sim > 0.8:
            matching_fields.append('cheque_number')
        similarity_scores.append(num_sim * weights['cheque_number'])
        
        # Amount similarity (exact or very close)
        amount1 = float(cheque1.get('amount', 0))
        amount2 = float(cheque2.get('amount', 0))
        if amount1 > 0 and amount2 > 0:
            amount_diff = abs(amount1 - amount2) / max(amount1, amount2)
            amount_sim = max(0, 1 - amount_diff)
            if amount_sim > 0.95:
                matching_fields.append('amount')
            similarity_scores.append(amount_sim * weights['amount'])
        
        # Client name similarity
        client_sim = self._string_similarity(cheque1.get('client_name', ''), 
                                           cheque2.get('client_name', ''))
        if client_sim > 0.8:
            matching_fields.append('client_name')
        similarity_scores.append(client_sim * weights['client_name'])
        
        # Bank information similarity
        bank_sim = self._string_similarity(
            f"{cheque1.get('bank_name', '')} {cheque1.get('branch_name', '')}",
            f"{cheque2.get('bank_name', '')} {cheque2.get('branch_name', '')}"
        )
        if bank_sim > 0.7:
            matching_fields.append('bank_info')
        similarity_scores.append(bank_sim * weights['bank_info'])
        
        # Date similarity
        date_sim = self._date_similarity(cheque1.get('issue_date'), cheque2.get('issue_date'))
        if date_sim > 0.8:
            matching_fields.append('dates')
        similarity_scores.append(date_sim * weights['dates'])
        
        # Additional information similarity
        additional_sim = self._string_similarity(
            f"{cheque1.get('depositor_name', '')} {cheque1.get('notes', '')}",
            f"{cheque2.get('depositor_name', '')} {cheque2.get('notes', '')}"
        )
        if additional_sim > 0.6:
            matching_fields.append('additional_info')
        similarity_scores.append(additional_sim * weights['additional_info'])
        
        # Calculate final score
        final_score = sum(similarity_scores)
        
        # Determine confidence and suggested action
        if final_score >= 0.95:
            confidence = 'very_high'
            suggested_action = 'merge_automatically'
        elif final_score >= 0.85:
            confidence = 'high'
            suggested_action = 'flag_for_review'
        elif final_score >= 0.75:
            confidence = 'medium'
            suggested_action = 'manual_verification'
        else:
            confidence = 'low'
            suggested_action = 'monitor'
        
        return {
            'score': final_score,
            'matching_fields': matching_fields,
            'confidence': confidence,
            'suggested_action': suggested_action
        }
    
    def _string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using difflib"""
        if not str1 or not str2:
            return 0.0
        
        return difflib.SequenceMatcher(None, str1.lower().strip(), str2.lower().strip()).ratio()
    
    def _date_similarity(self, date1: str, date2: str) -> float:
        """Calculate date similarity"""
        if not date1 or not date2:
            return 0.0
        
        try:
            d1 = datetime.strptime(date1, '%Y-%m-%d').date()
            d2 = datetime.strptime(date2, '%Y-%m-%d').date()
            
            diff_days = abs((d1 - d2).days)
            
            if diff_days == 0:
                return 1.0
            elif diff_days <= 1:
                return 0.9
            elif diff_days <= 7:
                return 0.7
            elif diff_days <= 30:
                return 0.5
            else:
                return 0.2
                
        except ValueError:
            return 0.0
    
    def _save_duplicate_detections(self, duplicates: List[DuplicateMatch]):
        """Save duplicate detection results to database"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            for duplicate in duplicates:
                cursor.execute("""
                    INSERT OR REPLACE INTO duplicate_detections
                    (cheque1_id, cheque2_id, similarity_score, matching_fields, 
                     confidence_level, suggested_action, detection_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    duplicate.cheque1_id, duplicate.cheque2_id, duplicate.similarity_score,
                    json.dumps(duplicate.matching_fields), duplicate.confidence_level,
                    duplicate.suggested_action, datetime.now()
                ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Saved {len(duplicates)} duplicate detection results")
            
        except Exception as e:
            self.logger.error(f"Error saving duplicate detections: {str(e)}")
    
    def execute_automation_rule(self, rule_id: str) -> Dict[str, Any]:
        """
        Execute a specific automation rule
        
        Args:
            rule_id: ID of the automation rule to execute
            
        Returns:
            Dictionary with execution results
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get rule details
            cursor.execute("""
                SELECT * FROM automation_rules WHERE id = ? AND active = 1
            """, (rule_id,))
            
            rule_data = cursor.fetchone()
            if not rule_data:
                return {'success': False, 'error': 'Rule not found or inactive'}
            
            rule = dict(rule_data)
            trigger_conditions = json.loads(rule['trigger_conditions'])
            actions = json.loads(rule['actions'])
            
            execution_results = []
            affected_records = 0
            
            # Execute each action
            for action in actions:
                action_result = self._execute_action(action, trigger_conditions)
                execution_results.append(action_result)
                affected_records += action_result.get('affected_records', 0)
            
            # Update last executed timestamp
            cursor.execute("""
                UPDATE automation_rules 
                SET last_executed = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (rule_id,))
            
            # Log execution
            cursor.execute("""
                INSERT INTO automation_logs 
                (rule_id, status, details, affected_records)
                VALUES (?, ?, ?, ?)
            """, (
                rule_id, 'success', 
                json.dumps(execution_results), 
                affected_records
            ))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'rule_id': rule_id,
                'execution_results': execution_results,
                'affected_records': affected_records
            }
            
        except Exception as e:
            self.logger.error(f"Error executing automation rule {rule_id}: {str(e)}")
            
            # Log error
            try:
                conn = self.get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO automation_logs 
                    (rule_id, status, details, affected_records)
                    VALUES (?, ?, ?, ?)
                """, (rule_id, 'error', str(e), 0))
                conn.commit()
                conn.close()
            except:
                pass
            
            return {'success': False, 'error': str(e)}
    
    def _execute_action(self, action: Dict[str, Any], conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific automation action"""
        action_type = action.get('type')
        
        try:
            if action_type == 'notification':
                return self._execute_notification_action(action, conditions)
            elif action_type == 'status_update':
                return self._execute_status_update_action(action, conditions)
            elif action_type == 'duplicate_check':
                return self._execute_duplicate_check_action(action, conditions)
            elif action_type == 'database_cleanup':
                return self._execute_database_cleanup_action(action, conditions)
            elif action_type == 'client_risk_update':
                return self._execute_client_risk_update_action(action, conditions)
            else:
                return {'success': False, 'error': f'Unknown action type: {action_type}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e), 'action_type': action_type}
    
    def _execute_notification_action(self, action: Dict[str, Any], conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Execute notification action"""
        # This would integrate with SMS/email services in production
        template_id = action.get('template')
        recipients = action.get('recipients', 'admin')
        
        # For now, just log the notification
        self.logger.info(f"Notification sent: template={template_id}, recipients={recipients}")
        
        return {
            'success': True,
            'action_type': 'notification',
            'template_id': template_id,
            'recipients': recipients,
            'affected_records': 1
        }
    
    def _execute_status_update_action(self, action: Dict[str, Any], conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Execute status update action"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            condition = action.get('condition', 'overdue')
            new_status = action.get('new_status', 'OVERDUE')
            
            if condition == 'overdue':
                # Update overdue cheques
                cursor.execute("""
                    UPDATE cheques 
                    SET status = ?, notes = COALESCE(notes, '') || ' [Auto-updated: Overdue]'
                    WHERE due_date < date('now') AND status = 'EN_ATTENTE'
                """, (new_status,))
            
            affected_rows = cursor.rowcount
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'action_type': 'status_update',
                'condition': condition,
                'new_status': new_status,
                'affected_records': affected_rows
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'action_type': 'status_update'}
    
    def _execute_duplicate_check_action(self, action: Dict[str, Any], conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Execute duplicate check action"""
        try:
            threshold = conditions.get('similarity_threshold', 0.85)
            duplicates = self.detect_advanced_duplicates(threshold)
            
            return {
                'success': True,
                'action_type': 'duplicate_check',
                'duplicates_found': len(duplicates),
                'affected_records': len(duplicates)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'action_type': 'duplicate_check'}
    
    def _execute_database_cleanup_action(self, action: Dict[str, Any], conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Execute database cleanup action"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cleanup_action = action.get('action', 'optimize_indexes')
            
            if cleanup_action == 'optimize_indexes':
                cursor.execute("VACUUM")
                cursor.execute("ANALYZE")
                cursor.execute("REINDEX")
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'action_type': 'database_cleanup',
                'cleanup_action': cleanup_action,
                'affected_records': 1
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'action_type': 'database_cleanup'}
    
    def _execute_client_risk_update_action(self, action: Dict[str, Any], conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Execute client risk update action"""
        # This would update client risk scores in a production system
        increment = action.get('increment', 10)
        
        return {
            'success': True,
            'action_type': 'client_risk_update',
            'risk_increment': increment,
            'affected_records': 1
        }
    
    def get_automation_status(self) -> Dict[str, Any]:
        """Get overall automation system status"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get active rules count
            cursor.execute("SELECT COUNT(*) as active_rules FROM automation_rules WHERE active = 1")
            active_rules = cursor.fetchone()['active_rules']
            
            # Get recent executions
            cursor.execute("""
                SELECT COUNT(*) as recent_executions 
                FROM automation_logs 
                WHERE execution_time >= datetime('now', '-24 hours')
            """)
            recent_executions = cursor.fetchone()['recent_executions']
            
            # Get duplicate detections
            cursor.execute("""
                SELECT COUNT(*) as pending_duplicates 
                FROM duplicate_detections 
                WHERE resolved = 0
            """)
            pending_duplicates = cursor.fetchone()['pending_duplicates']
            
            conn.close()
            
            return {
                'active_rules': active_rules,
                'recent_executions': recent_executions,
                'pending_duplicates': pending_duplicates,
                'system_status': 'active',
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting automation status: {str(e)}")
            return {
                'system_status': 'error',
                'error': str(e)
            }