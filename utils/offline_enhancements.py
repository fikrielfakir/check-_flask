"""
Offline desktop enhancements for the cheque management system.
Additional utilities for Windows desktop optimization.
"""

import os
import sys
import platform
import subprocess
import logging
from datetime import datetime
import shutil
import sqlite3

class OfflineEnhancements:
    """Utilities for offline desktop operation"""
    
    def __init__(self, app_config):
        """
        Initialize offline enhancements
        
        Args:
            app_config: Flask app configuration object
        """
        self.app_config = app_config
        self.data_dir = os.path.join(os.getcwd(), "data")
        self.backup_dir = os.path.join(self.data_dir, "backups")
        self.logs_dir = os.path.join(self.data_dir, "logs")
        
        # Ensure directories exist
        for directory in [self.data_dir, self.backup_dir, self.logs_dir]:
            os.makedirs(directory, exist_ok=True)
        
        logging.info("Offline enhancements initialized")
    
    def is_windows(self) -> bool:
        """Check if running on Windows"""
        return platform.system() == 'Windows'
    
    def open_file_explorer(self, path: str) -> bool:
        """
        Open file explorer at specified path
        
        Args:
            path (str): Directory path to open
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.is_windows():
                subprocess.run(['explorer', os.path.normpath(path)], check=True)
                return True
            else:
                logging.warning("File explorer opening only supported on Windows")
                return False
        except Exception as e:
            logging.error(f"Error opening file explorer: {str(e)}")
            return False
    
    def create_desktop_shortcut(self, target_url: str = "http://localhost:5000") -> bool:
        """
        Create desktop shortcut for the application (Windows only)
        
        Args:
            target_url (str): URL to open in browser
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.is_windows():
                logging.warning("Desktop shortcuts only supported on Windows")
                return False
            
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            path = os.path.join(desktop, "Gestionnaire de Chèques.lnk")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = "C:\\Program Files\\Internet Explorer\\iexplore.exe"
            shortcut.Arguments = target_url
            shortcut.WorkingDirectory = os.getcwd()
            shortcut.IconLocation = "C:\\Program Files\\Internet Explorer\\iexplore.exe,0"
            shortcut.save()
            
            logging.info(f"Desktop shortcut created: {path}")
            return True
            
        except ImportError:
            logging.warning("Windows shell modules not available")
            return False
        except Exception as e:
            logging.error(f"Error creating desktop shortcut: {str(e)}")
            return False
    
    def backup_all_data(self) -> str:
        """
        Create comprehensive backup of all application data
        
        Returns:
            str: Path to backup file
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"cheques_backup_{timestamp}"
            backup_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
            
            import zipfile
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup database
                db_path = os.path.join(self.data_dir, "cheques.db")
                if os.path.exists(db_path):
                    zipf.write(db_path, "cheques.db")
                
                # Backup Excel files
                excel_dir = self.app_config.get('EXCEL_FOLDER')
                if os.path.exists(excel_dir):
                    for root, dirs, files in os.walk(excel_dir):
                        for file in files:
                            if file.endswith('.xlsx'):
                                file_path = os.path.join(root, file)
                                arcname = os.path.join("excel", os.path.relpath(file_path, excel_dir))
                                zipf.write(file_path, arcname)
                
                # Backup uploads
                uploads_dir = self.app_config.get('UPLOAD_FOLDER')
                if os.path.exists(uploads_dir):
                    for root, dirs, files in os.walk(uploads_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.join("uploads", os.path.relpath(file_path, uploads_dir))
                            zipf.write(file_path, arcname)
                
                # Backup exports
                exports_dir = self.app_config.get('EXPORTS_FOLDER')
                if os.path.exists(exports_dir):
                    for root, dirs, files in os.walk(exports_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.join("exports", os.path.relpath(file_path, exports_dir))
                            zipf.write(file_path, arcname)
            
            logging.info(f"Complete backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logging.error(f"Error creating backup: {str(e)}")
            raise
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """
        Restore application data from backup
        
        Args:
            backup_path (str): Path to backup zip file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            import zipfile
            
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            # Create restore timestamp
            restore_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Backup current data before restore
            current_backup = f"pre_restore_backup_{restore_timestamp}.zip"
            current_backup_path = os.path.join(self.backup_dir, current_backup)
            self.backup_all_data()  # This will create the current backup
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Restore database
                if "cheques.db" in zipf.namelist():
                    db_path = os.path.join(self.data_dir, "cheques.db")
                    with open(db_path, 'wb') as f:
                        f.write(zipf.read("cheques.db"))
                
                # Restore Excel files
                excel_dir = self.app_config.get('EXCEL_FOLDER')
                for file_info in zipf.infolist():
                    if file_info.filename.startswith('excel/'):
                        target_path = os.path.join(excel_dir, 
                                                 os.path.relpath(file_info.filename, 'excel'))
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with open(target_path, 'wb') as f:
                            f.write(zipf.read(file_info.filename))
                
                # Restore uploads
                uploads_dir = self.app_config.get('UPLOAD_FOLDER')
                for file_info in zipf.infolist():
                    if file_info.filename.startswith('uploads/'):
                        target_path = os.path.join(uploads_dir, 
                                                 os.path.relpath(file_info.filename, 'uploads'))
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with open(target_path, 'wb') as f:
                            f.write(zipf.read(file_info.filename))
            
            logging.info(f"Data restored from backup: {backup_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error restoring from backup: {str(e)}")
            return False
    
    def get_system_info(self) -> dict:
        """
        Get system information for diagnostics
        
        Returns:
            dict: System information
        """
        try:
            info = {
                'platform': platform.platform(),
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': sys.version,
                'working_directory': os.getcwd(),
                'data_directory': self.data_dir,
                'disk_space': self._get_disk_space()
            }
            return info
        except Exception as e:
            logging.error(f"Error getting system info: {str(e)}")
            return {}
    
    def _get_disk_space(self) -> dict:
        """Get disk space information"""
        try:
            if self.is_windows():
                import shutil
                total, used, free = shutil.disk_usage(os.getcwd())
                return {
                    'total_gb': total // (1024**3),
                    'used_gb': used // (1024**3),
                    'free_gb': free // (1024**3)
                }
            else:
                return {'error': 'Disk space info only available on Windows'}
        except Exception as e:
            return {'error': str(e)}
    
    def cleanup_old_backups(self, keep_days: int = 30) -> int:
        """
        Clean up old backup files
        
        Args:
            keep_days (int): Number of days to keep backups
            
        Returns:
            int: Number of files deleted
        """
        try:
            deleted_count = 0
            cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 3600)
            
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.zip'):
                    file_path = os.path.join(self.backup_dir, filename)
                    if os.path.getmtime(file_path) < cutoff_time:
                        os.remove(file_path)
                        deleted_count += 1
                        logging.info(f"Deleted old backup: {filename}")
            
            return deleted_count
            
        except Exception as e:
            logging.error(f"Error cleaning up backups: {str(e)}")
            return 0
    
    def optimize_database(self) -> bool:
        """
        Optimize SQLite database performance
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db_path = os.path.join(self.data_dir, "cheques.db")
            
            if not os.path.exists(db_path):
                logging.warning("Database file not found for optimization")
                return False
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Run optimization commands
            cursor.execute("VACUUM")
            cursor.execute("ANALYZE")
            cursor.execute("REINDEX")
            
            conn.commit()
            conn.close()
            
            logging.info("Database optimization completed")
            return True
            
        except Exception as e:
            logging.error(f"Error optimizing database: {str(e)}")
            return False
    
    def generate_diagnostic_report(self) -> str:
        """
        Generate comprehensive diagnostic report
        
        Returns:
            str: Path to diagnostic report file
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_filename = f"diagnostic_report_{timestamp}.txt"
            report_path = os.path.join(self.logs_dir, report_filename)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(f"Diagnostic Report - Gestionnaire de Chèques\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")
                
                # System Information
                f.write("SYSTEM INFORMATION:\n")
                f.write("-" * 20 + "\n")
                system_info = self.get_system_info()
                for key, value in system_info.items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")
                
                # Database Information
                f.write("DATABASE INFORMATION:\n")
                f.write("-" * 20 + "\n")
                db_path = os.path.join(self.data_dir, "cheques.db")
                if os.path.exists(db_path):
                    db_size = os.path.getsize(db_path)
                    f.write(f"Database path: {db_path}\n")
                    f.write(f"Database size: {db_size / 1024:.1f} KB\n")
                    
                    # Get table counts
                    try:
                        conn = sqlite3.connect(db_path)
                        cursor = conn.cursor()
                        
                        tables = ['cheques', 'clients', 'users', 'banks', 'branches']
                        for table in tables:
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            count = cursor.fetchone()[0]
                            f.write(f"{table} count: {count}\n")
                        
                        conn.close()
                    except Exception as e:
                        f.write(f"Error reading database: {str(e)}\n")
                else:
                    f.write("Database file not found\n")
                f.write("\n")
                
                # File System Information
                f.write("FILE SYSTEM INFORMATION:\n")
                f.write("-" * 25 + "\n")
                
                directories = [
                    ('Data Directory', self.data_dir),
                    ('Excel Directory', self.app_config.get('EXCEL_FOLDER', 'N/A')),
                    ('Upload Directory', self.app_config.get('UPLOAD_FOLDER', 'N/A')),
                    ('Export Directory', self.app_config.get('EXPORTS_FOLDER', 'N/A'))
                ]
                
                for name, path in directories:
                    if path != 'N/A' and os.path.exists(path):
                        file_count = len(os.listdir(path))
                        f.write(f"{name}: {path} ({file_count} files)\n")
                    else:
                        f.write(f"{name}: {path} (not found)\n")
                
                f.write("\n")
                f.write("Report generation completed successfully.\n")
            
            logging.info(f"Diagnostic report generated: {report_path}")
            return report_path
            
        except Exception as e:
            logging.error(f"Error generating diagnostic report: {str(e)}")
            raise