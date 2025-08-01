"""
Automatic Excel synchronization utility for cheque operations.
Ensures Excel files are always up-to-date with database changes.
"""

import logging
from datetime import datetime
from utils.excel_manager import ExcelManager
from utils.excel_yearly_manager import ExcelYearlyManager

class ChequeExcelSync:
    """Handles automatic synchronization between database and Excel files"""
    
    def __init__(self, excel_folder_path):
        self.excel_manager = ExcelManager()
        self.yearly_manager = ExcelYearlyManager(excel_folder_path)
        self.logger = logging.getLogger(__name__)
    
    def sync_cheque_to_excel(self, cheque, operation='create'):
        """
        Synchronize a cheque to Excel files
        
        Args:
            cheque: Cheque model instance
            operation: 'create', 'update', or 'delete'
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if operation == 'delete':
                return self._handle_cheque_deletion(cheque)
            else:
                return self._handle_cheque_upsert(cheque)
                
        except Exception as e:
            self.logger.error(f"Error syncing cheque to Excel: {str(e)}")
            return False
    
    def _handle_cheque_upsert(self, cheque):
        """Handle cheque creation or update"""
        try:
            # Prepare data for Excel
            excel_data = self._convert_cheque_to_excel_format(cheque)
            
            # Sync with both managers for redundancy
            primary_success = self.excel_manager.add_or_update_cheque(cheque)
            secondary_success = self.yearly_manager.add_or_update_cheque(excel_data)
            
            if primary_success or secondary_success:
                self.logger.info(f"Successfully synced cheque {cheque.id} to Excel")
                return True
            else:
                self.logger.warning(f"Failed to sync cheque {cheque.id} to Excel")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in cheque upsert: {str(e)}")
            return False
    
    def _handle_cheque_deletion(self, cheque):
        """Handle cheque deletion from Excel"""
        try:
            if not cheque.cheque_number or not cheque.branch:
                return True  # Nothing to delete if no number or bank
            
            success = self.excel_manager.remove_cheque_from_excel(
                cheque.cheque_number,
                cheque.branch.bank.name,
                cheque.due_date.year
            )
            
            if success:
                self.logger.info(f"Successfully removed cheque {cheque.id} from Excel")
            else:
                self.logger.warning(f"Could not find cheque {cheque.id} in Excel files")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error in cheque deletion: {str(e)}")
            return False
    
    def _convert_cheque_to_excel_format(self, cheque):
        """Convert cheque model to Excel data format"""
        return {
            'date_emission': cheque.issue_date.strftime('%d/%m/%Y') if cheque.issue_date else '',
            'type': cheque.payment_type or 'CHQ',
            'numero': cheque.cheque_number or '',
            'banque': f"{cheque.branch.bank.name} - {cheque.branch.name}" if cheque.branch else '',
            'banque_depot': f"{cheque.deposit_branch.bank.name} - {cheque.deposit_branch.name}" if cheque.deposit_branch else '',
            'propriétaire': cheque.client.name if cheque.client else '',
            'deposant': cheque.depositor_name or '',
            'montant': float(cheque.amount),
            'devise': cheque.currency or 'MAD',
            'echeance_date': cheque.due_date,
            'date_creation': cheque.created_date.strftime('%d/%m/%Y') if cheque.created_date else '',
            'statut': cheque.status or 'EN ATTENTE',
            'numero_facture': cheque.invoice_number or '',
            'date_facture': cheque.invoice_date.strftime('%d/%m/%Y') if cheque.invoice_date else '',
            'notes': cheque.notes or ''
        }
    
    def bulk_sync_all_cheques(self, cheques_query=None):
        """
        Bulk synchronize all cheques to Excel files
        
        Args:
            cheques_query: Optional query to filter cheques
            
        Returns:
            dict: Sync results
        """
        from models import Cheque
        
        if cheques_query is None:
            cheques = Cheque.query.all()
        else:
            cheques = cheques_query.all()
        
        sync_results = {
            'total_cheques': len(cheques),
            'successful_syncs': 0,
            'failed_syncs': 0,
            'errors': []
        }
        
        for cheque in cheques:
            try:
                if self.sync_cheque_to_excel(cheque, 'update'):
                    sync_results['successful_syncs'] += 1
                else:
                    sync_results['failed_syncs'] += 1
                    
            except Exception as e:
                sync_results['failed_syncs'] += 1
                sync_results['errors'].append(f"Cheque {cheque.id}: {str(e)}")
        
        self.logger.info(f"Bulk sync completed: {sync_results['successful_syncs']}/{sync_results['total_cheques']} successful")
        return sync_results
    
    def verify_excel_integrity(self, year=None):
        """
        Verify integrity of Excel files against database
        
        Args:
            year: Optional year to check, defaults to current year
            
        Returns:
            dict: Integrity check results
        """
        if year is None:
            year = datetime.now().year
        
        try:
            file_stats = self.excel_manager.get_file_statistics(year)
            
            if not file_stats:
                return {
                    'status': 'missing',
                    'message': f'Excel file for year {year} does not exist'
                }
            
            # Compare with database count
            from models import Cheque
            db_count = Cheque.query.filter(
                Cheque.due_date >= datetime(year, 1, 1).date(),
                Cheque.due_date < datetime(year + 1, 1, 1).date()
            ).count()
            
            excel_count = file_stats['total_cheques']
            
            return {
                'status': 'verified',
                'year': year,
                'database_count': db_count,
                'excel_count': excel_count,
                'difference': abs(db_count - excel_count),
                'in_sync': db_count == excel_count,
                'file_stats': file_stats
            }
            
        except Exception as e:
            self.logger.error(f"Error verifying Excel integrity: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }