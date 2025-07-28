"""
Local SQLite Database Manager for offline desktop operations.
Provides advanced querying, statistics, and data management capabilities.
"""

import sqlite3
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import logging

class DatabaseManager:
    """Local SQLite database manager for cheque management system"""
    
    def __init__(self, db_path: str):
        """
        Initialize database manager
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._ensure_tables()
        self._ensure_indexes()
        logging.info(f"Database manager initialized: {db_path}")
    
    def _ensure_tables(self):
        """Ensure all required tables exist with proper structure"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create cheques table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cheques (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero TEXT NOT NULL,
                    banque TEXT NOT NULL,
                    proprietaire TEXT NOT NULL,
                    deposant TEXT,
                    montant REAL NOT NULL,
                    date_emission DATE NOT NULL,
                    date_echeance DATE NOT NULL,
                    type TEXT DEFAULT 'CHQ',
                    statut TEXT DEFAULT 'EN_ATTENTE',
                    notes TEXT,
                    recipient_name TEXT,
                    exported BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create export history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS export_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    export_type TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    export_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    record_count INTEGER DEFAULT 0,
                    file_path TEXT
                )
            ''')
            
            # Create settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Add new columns if they don't exist
            self._add_column_if_not_exists(cursor, 'cheques', 'recipient_name', 'TEXT')
            self._add_column_if_not_exists(cursor, 'cheques', 'exported', 'BOOLEAN DEFAULT 0')
            
            conn.commit()
    
    def _add_column_if_not_exists(self, cursor, table_name: str, column_name: str, column_type: str):
        """Add column to table if it doesn't exist"""
        try:
            cursor.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}')
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                logging.warning(f"Error adding column {column_name}: {e}")
    
    def _ensure_indexes(self):
        """Create indexes for better query performance"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_cheque_numero_banque ON cheques(numero, banque)",
                "CREATE INDEX IF NOT EXISTS idx_cheque_date_echeance ON cheques(date_echeance)",
                "CREATE INDEX IF NOT EXISTS idx_cheque_statut ON cheques(statut)",
                "CREATE INDEX IF NOT EXISTS idx_cheque_proprietaire ON cheques(proprietaire)",
                "CREATE INDEX IF NOT EXISTS idx_cheque_exported ON cheques(exported)"
            ]
            
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except sqlite3.OperationalError as e:
                    logging.warning(f"Index creation warning: {e}")
            
            conn.commit()
    
    def insert_cheque(self, cheque_data: Dict) -> bool:
        """
        Insert a new cheque record
        
        Args:
            cheque_data (dict): Cheque information
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO cheques (
                        numero, banque, proprietaire, deposant, montant,
                        date_emission, date_echeance, type, statut, notes, recipient_name
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    cheque_data.get('numero'),
                    cheque_data.get('banque'),
                    cheque_data.get('proprietaire'),
                    cheque_data.get('deposant'),
                    cheque_data.get('montant'),
                    cheque_data.get('date_emission'),
                    cheque_data.get('date_echeance'),
                    cheque_data.get('type', 'CHQ'),
                    cheque_data.get('statut', 'EN_ATTENTE'),
                    cheque_data.get('notes'),
                    cheque_data.get('recipient_name')
                ))
                
                conn.commit()
                logging.info(f"Inserted cheque: {cheque_data.get('numero')}")
                return True
                
        except sqlite3.Error as e:
            logging.error(f"Error inserting cheque: {e}")
            return False
    
    def update_cheque(self, cheque_id: int, cheque_data: Dict) -> bool:
        """
        Update an existing cheque record
        
        Args:
            cheque_id (int): Cheque ID
            cheque_data (dict): Updated cheque information
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE cheques SET
                        numero = ?, banque = ?, proprietaire = ?, deposant = ?,
                        montant = ?, date_emission = ?, date_echeance = ?,
                        type = ?, statut = ?, notes = ?, recipient_name = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    cheque_data.get('numero'),
                    cheque_data.get('banque'),
                    cheque_data.get('proprietaire'),
                    cheque_data.get('deposant'),
                    cheque_data.get('montant'),
                    cheque_data.get('date_emission'),
                    cheque_data.get('date_echeance'),
                    cheque_data.get('type'),
                    cheque_data.get('statut'),
                    cheque_data.get('notes'),
                    cheque_data.get('recipient_name'),
                    cheque_id
                ))
                
                conn.commit()
                logging.info(f"Updated cheque ID: {cheque_id}")
                return True
                
        except sqlite3.Error as e:
            logging.error(f"Error updating cheque: {e}")
            return False
    
    def delete_cheque(self, cheque_id: int) -> bool:
        """
        Delete a cheque record
        
        Args:
            cheque_id (int): Cheque ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM cheques WHERE id = ?', (cheque_id,))
                conn.commit()
                logging.info(f"Deleted cheque ID: {cheque_id}")
                return True
                
        except sqlite3.Error as e:
            logging.error(f"Error deleting cheque: {e}")
            return False
    
    def update_cheque_status(self, cheque_id: int, status: str) -> bool:
        """
        Update cheque status
        
        Args:
            cheque_id (int): Cheque ID
            status (str): New status
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE cheques SET statut = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, cheque_id))
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            logging.error(f"Error updating status: {e}")
            return False
    
    def mark_exported(self, cheque_ids: List[int]) -> bool:
        """
        Mark cheques as exported
        
        Args:
            cheque_ids (list): List of cheque IDs
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                placeholders = ','.join(['?' for _ in cheque_ids])
                cursor.execute(f'''
                    UPDATE cheques SET exported = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE id IN ({placeholders})
                ''', cheque_ids)
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            logging.error(f"Error marking as exported: {e}")
            return False
    
    def check_duplicate(self, numero: str, banque: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if a cheque number/bank combination already exists
        
        Args:
            numero (str): Cheque number
            banque (str): Bank name
            exclude_id (int, optional): ID to exclude from check
            
        Returns:
            bool: True if duplicate exists, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if exclude_id:
                    cursor.execute('''
                        SELECT COUNT(*) FROM cheques 
                        WHERE numero = ? AND banque = ? AND id != ?
                    ''', (numero, banque, exclude_id))
                else:
                    cursor.execute('''
                        SELECT COUNT(*) FROM cheques 
                        WHERE numero = ? AND banque = ?
                    ''', (numero, banque))
                
                count = cursor.fetchone()[0]
                return count > 0
                
        except sqlite3.Error as e:
            logging.error(f"Error checking duplicate: {e}")
            return False
    
    def get_cheques(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Get cheques with optional filters
        
        Args:
            filters (dict, optional): Filter criteria including:
                - exported: bool
                - year: int
                - month: int
                - type: str (CHQ/LCN)
                - proprietaire: str
                - banque: str
                - statut: str
                - limit: int
                - offset: int
                
        Returns:
            list: List of cheque dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Enable column access by name
                cursor = conn.cursor()
                
                # Build query with filters
                where_clauses = []
                params = []
                
                if filters:
                    if 'exported' in filters:
                        where_clauses.append('exported = ?')
                        params.append(1 if filters['exported'] else 0)
                    
                    if 'year' in filters:
                        where_clauses.append('strftime("%Y", date_echeance) = ?')
                        params.append(str(filters['year']))
                    
                    if 'month' in filters:
                        where_clauses.append('strftime("%m", date_echeance) = ?')
                        params.append(f"{filters['month']:02d}")
                    
                    if 'type' in filters:
                        where_clauses.append('type = ?')
                        params.append(filters['type'])
                    
                    if 'proprietaire' in filters:
                        where_clauses.append('proprietaire LIKE ?')
                        params.append(f"%{filters['proprietaire']}%")
                    
                    if 'banque' in filters:
                        where_clauses.append('banque LIKE ?')
                        params.append(f"%{filters['banque']}%")
                    
                    if 'statut' in filters:
                        where_clauses.append('statut = ?')
                        params.append(filters['statut'])
                
                # Build final query
                query = 'SELECT * FROM cheques'
                if where_clauses:
                    query += ' WHERE ' + ' AND '.join(where_clauses)
                
                query += ' ORDER BY date_echeance DESC'
                
                # Add limit and offset if specified
                if filters and 'limit' in filters:
                    query += f' LIMIT {filters["limit"]}'
                    if 'offset' in filters:
                        query += f' OFFSET {filters["offset"]}'
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                return [dict(row) for row in rows]
                
        except sqlite3.Error as e:
            logging.error(f"Error getting cheques: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """
        Get comprehensive database statistics
        
        Returns:
            dict: Statistics including counts, sums, averages, etc.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Basic counts and sums
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_count,
                        SUM(montant) as total_amount,
                        AVG(montant) as average_amount,
                        MIN(montant) as min_amount,
                        MAX(montant) as max_amount
                    FROM cheques
                ''')
                row = cursor.fetchone()
                stats.update({
                    'total_count': row[0] or 0,
                    'total_amount': row[1] or 0.0,
                    'average_amount': row[2] or 0.0,
                    'min_amount': row[3] or 0.0,
                    'max_amount': row[4] or 0.0
                })
                
                # Count by type
                cursor.execute('SELECT type, COUNT(*) FROM cheques GROUP BY type')
                type_counts = dict(cursor.fetchall())
                stats['count_by_type'] = type_counts
                
                # Count by status
                cursor.execute('SELECT statut, COUNT(*) FROM cheques GROUP BY statut')
                status_counts = dict(cursor.fetchall())
                stats['count_by_status'] = status_counts
                
                # Pending exports
                cursor.execute('SELECT COUNT(*) FROM cheques WHERE exported = 0')
                stats['pending_exports'] = cursor.fetchone()[0] or 0
                
                # Years with data
                cursor.execute('SELECT COUNT(DISTINCT strftime("%Y", date_echeance)) FROM cheques')
                stats['years_with_data'] = cursor.fetchone()[0] or 0
                
                return stats
                
        except sqlite3.Error as e:
            logging.error(f"Error getting statistics: {e}")
            return {}
    
    def get_years(self) -> List[int]:
        """
        Get list of years with cheque data
        
        Returns:
            list: Sorted list of years (integers)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT strftime("%Y", date_echeance) as year 
                    FROM cheques 
                    ORDER BY year DESC
                ''')
                return [int(row[0]) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            logging.error(f"Error getting years: {e}")
            return []
    
    def get_banks(self) -> List[str]:
        """
        Get list of unique bank names
        
        Returns:
            list: Sorted list of bank names
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT DISTINCT banque FROM cheques ORDER BY banque')
                return [row[0] for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            logging.error(f"Error getting banks: {e}")
            return []
    
    def add_export_record(self, export_type: str, filename: str, record_count: int, file_path: str = None) -> bool:
        """
        Add export history record
        
        Args:
            export_type (str): Type of export (Excel, PDF, CSV)
            filename (str): Generated filename
            record_count (int): Number of records exported
            file_path (str, optional): Full file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO export_history (export_type, filename, record_count, file_path)
                    VALUES (?, ?, ?, ?)
                ''', (export_type, filename, record_count, file_path))
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            logging.error(f"Error adding export record: {e}")
            return False
    
    def get_export_history(self, limit: int = 50) -> List[Dict]:
        """
        Get export history
        
        Args:
            limit (int): Maximum number of records to return
            
        Returns:
            list: List of export history dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM export_history 
                    ORDER BY export_date DESC 
                    LIMIT ?
                ''', (limit,))
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            logging.error(f"Error getting export history: {e}")
            return []
    
    def vacuum_database(self) -> bool:
        """
        Vacuum database to reclaim space and optimize performance
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('VACUUM')
                logging.info("Database vacuumed successfully")
                return True
                
        except sqlite3.Error as e:
            logging.error(f"Error vacuuming database: {e}")
            return False
    
    def backup_database(self, backup_path: str) -> bool:
        """
        Create a backup of the database
        
        Args:
            backup_path (str): Path for backup file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logging.info(f"Database backed up to: {backup_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error backing up database: {e}")
            return False