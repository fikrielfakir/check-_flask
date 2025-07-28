import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import datetime
import tempfile
import os
from pathlib import Path

class ExcelManager:
    def __init__(self):
        self.upload_dir = Path("uploads/excel")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Excel headers
        self.headers = [
            "Date de reception",
            "Reg",
            "N°",
            "Banque",
            "Nom et prénom / Raison sociale",
            "Nom du Déposant",
            "Le montant",
            "Echeance",
            "N° Facture",
            "Date de Fac",
            "Statut du Chèque"
        ]
        
        # Month names
        self.month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
    
    def get_excel_filename(self, year):
        """Get Excel filename for a specific year"""
        return self.upload_dir / f"cheques_{year}.xlsx"
    
    def ensure_file_exists(self, year):
        """Ensure Excel file exists for the year"""
        filename = self.get_excel_filename(year)
        
        if not filename.exists():
            self.create_yearly_file(year)
        
        return filename
    
    def create_yearly_file(self, year):
        """Create a new yearly Excel file with monthly sheets"""
        filename = self.get_excel_filename(year)
        workbook = openpyxl.Workbook()
        
        # Remove default sheet
        workbook.remove(workbook.active)
        
        # Create 12 monthly sheets
        for month_name in self.month_names:
            sheet = workbook.create_sheet(title=month_name)
            self._setup_sheet_headers(sheet)
        
        workbook.save(filename)
        return filename
    
    def _setup_sheet_headers(self, sheet):
        """Setup headers and formatting for a sheet"""
        # Add headers
        for col, header in enumerate(self.headers, 1):
            cell = sheet.cell(row=1, column=col, value=header)
            
            # Header formatting
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = Border(
                left=Side(style="thin"),
                right=Side(style="thin"),
                top=Side(style="thin"),
                bottom=Side(style="thin")
            )
        
        # Set column widths
        column_widths = [15, 8, 15, 15, 30, 30, 12, 15, 15, 15, 15]
        for col, width in enumerate(column_widths, 1):
            sheet.column_dimensions[openpyxl.utils.get_column_letter(col)].width = width
        
        # Freeze header row
        sheet.freeze_panes = "A2"
    
    def add_or_update_cheque(self, cheque):
        """Add or update a cheque in Excel"""
        year = cheque.due_date.year
        month = cheque.due_date.month
        
        filename = self.ensure_file_exists(year)
        workbook = openpyxl.load_workbook(filename)
        
        month_name = self.month_names[month - 1]
        if month_name not in workbook.sheetnames:
            sheet = workbook.create_sheet(title=month_name)
            self._setup_sheet_headers(sheet)
        else:
            sheet = workbook[month_name]
        
        # Find existing row or get next empty row
        existing_row = self._find_existing_cheque(sheet, cheque.cheque_number, cheque.branch.bank.name)
        if existing_row:
            row_num = existing_row
        else:
            row_num = self._get_next_empty_row(sheet)
        
        # Prepare data
        data = [
            cheque.created_at.strftime('%d/%m/%Y'),
            row_num - 1,  # Registration number
            cheque.cheque_number or '',
            cheque.branch.bank.name,
            cheque.client.name,
            cheque.depositor_name or '',
            float(cheque.amount),
            cheque.due_date.strftime('%d/%m/%Y'),
            cheque.invoice_number or '',
            cheque.invoice_date.strftime('%d/%m/%Y') if cheque.invoice_date else '',
            cheque.status_text
        ]
        
        # Write data to row
        for col, value in enumerate(data, 1):
            cell = sheet.cell(row=row_num, column=col, value=value)
            
            # Apply borders
            cell.border = Border(
                left=Side(style="thin"),
                right=Side(style="thin"),
                top=Side(style="thin"),
                bottom=Side(style="thin")
            )
            
            # Format amount column
            if col == 7:  # Amount column
                cell.number_format = '#,##0.00'
        
        workbook.save(filename)
    
    def _find_existing_cheque(self, sheet, cheque_number, bank_name):
        """Find existing cheque row"""
        if not cheque_number:
            return None
        
        for row in range(2, sheet.max_row + 1):
            if (sheet.cell(row=row, column=3).value == cheque_number and 
                sheet.cell(row=row, column=4).value == bank_name):
                return row
        return None
    
    def _get_next_empty_row(self, sheet):
        """Get next empty row"""
        return sheet.max_row + 1
    
    def export_cheques(self, cheques, date_from=None, date_to=None):
        """Export cheques to Excel file"""
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_file.close()
        
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Export Chèques"
        
        # Setup headers
        self._setup_sheet_headers(sheet)
        
        # Add data
        for idx, cheque in enumerate(cheques, 2):
            data = [
                cheque.created_at.strftime('%d/%m/%Y'),
                idx - 1,
                cheque.cheque_number or '',
                cheque.branch.bank.name,
                cheque.client.name,
                cheque.depositor_name or '',
                float(cheque.amount),
                cheque.due_date.strftime('%d/%m/%Y'),
                cheque.invoice_number or '',
                cheque.invoice_date.strftime('%d/%m/%Y') if cheque.invoice_date else '',
                cheque.status_text
            ]
            
            for col, value in enumerate(data, 1):
                cell = sheet.cell(row=idx, column=col, value=value)
                cell.border = Border(
                    left=Side(style="thin"),
                    right=Side(style="thin"),
                    top=Side(style="thin"),
                    bottom=Side(style="thin")
                )
                
                if col == 7:  # Amount column
                    cell.number_format = '#,##0.00'
        
        workbook.save(temp_file.name)
        return temp_file.name
