from models import Cheque, Notification, User
from app import db
from datetime import date, timedelta
import logging

class NotificationManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def check_due_cheques(self):
        """Check for cheques due in next 3 days"""
        today = date.today()
        due_date = today + timedelta(days=3)
        
        # Find cheques due soon
        due_cheques = Cheque.query.filter(
            Cheque.due_date.between(today, due_date),
            Cheque.status.in_(['en_attente', 'depose'])
        ).all()
        
        self.logger.info(f"Found {len(due_cheques)} cheques due in next 3 days")
        
        for cheque in due_cheques:
            self._create_due_notification(cheque)
    
    def check_rejected_cheques(self):
        """Check for rejected cheques without treatment"""
        rejected_cheques = Cheque.query.filter(
            Cheque.status == 'rejete'
        ).all()
        
        self.logger.info(f"Found {len(rejected_cheques)} rejected cheques")
        
        for cheque in rejected_cheques:
            # Check if notification already exists for this cheque today
            today = date.today()
            existing = Notification.query.filter(
                Notification.cheque_id == cheque.id,
                Notification.type == 'rejected',
                db.func.date(Notification.created_at) == today
            ).first()
            
            if not existing:
                self._create_rejected_notification(cheque)
    
    def check_overdue_cheques(self):
        """Check for overdue cheques"""
        today = date.today()
        
        overdue_cheques = Cheque.query.filter(
            Cheque.due_date < today,
            Cheque.status.in_(['en_attente', 'depose'])
        ).all()
        
        self.logger.info(f"Found {len(overdue_cheques)} overdue cheques")
        
        for cheque in overdue_cheques:
            self._create_overdue_notification(cheque)
    
    def _create_due_notification(self, cheque):
        """Create notification for cheque due soon"""
        # Check if notification already exists
        existing = Notification.query.filter(
            Notification.cheque_id == cheque.id,
            Notification.type == 'due_soon',
            db.func.date(Notification.created_at) == date.today()
        ).first()
        
        if not existing:
            notification = Notification(
                type='due_soon',
                title='Chèque à échéance proche',
                message=f'Le chèque n°{cheque.cheque_number} de {cheque.client.name} arrive à échéance le {cheque.due_date.strftime("%d/%m/%Y")}',
                cheque_id=cheque.id
            )
            db.session.add(notification)
            self.logger.info(f"Created due notification for cheque {cheque.id}")
    
    def _create_rejected_notification(self, cheque):
        """Create notification for rejected cheque"""
        notification = Notification(
            type='rejected',
            title='Chèque rejeté sans traitement',
            message=f'Le chèque n°{cheque.cheque_number} de {cheque.client.name} est rejeté et nécessite un traitement',
            cheque_id=cheque.id
        )
        db.session.add(notification)
        self.logger.info(f"Created rejected notification for cheque {cheque.id}")
    
    def _create_overdue_notification(self, cheque):
        """Create notification for overdue cheque"""
        # Check if notification already exists
        existing = Notification.query.filter(
            Notification.cheque_id == cheque.id,
            Notification.type == 'overdue',
            db.func.date(Notification.created_at) == date.today()
        ).first()
        
        if not existing:
            days_overdue = (date.today() - cheque.due_date).days
            notification = Notification(
                type='overdue',
                title='Chèque en retard',
                message=f'Le chèque n°{cheque.cheque_number} de {cheque.client.name} est en retard de {days_overdue} jour(s)',
                cheque_id=cheque.id
            )
            db.session.add(notification)
            self.logger.info(f"Created overdue notification for cheque {cheque.id}")
    
    def run_daily_checks(self):
        """Run all daily notification checks"""
        try:
            self.check_due_cheques()
            self.check_rejected_cheques()
            self.check_overdue_cheques()
            db.session.commit()
            self.logger.info("Daily notification checks completed successfully")
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error during daily notification checks: {str(e)}")
