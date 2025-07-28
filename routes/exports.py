from flask import Blueprint, render_template, request, send_file, flash, current_app
from flask_login import login_required
from models import Cheque, Client, Branch, Bank
from app import db
from datetime import datetime, date
from utils.excel_manager import ExcelManager
from utils.pdf_generator import PDFGenerator
import tempfile
import os

exports_bp = Blueprint('exports', __name__)

@exports_bp.route('/')
@login_required
def index():
    banks = Bank.query.all()
    return render_template('exports/index.html', banks=banks)

@exports_bp.route('/excel', methods=['POST'])
@login_required
def export_excel():
    # Get filter parameters
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    bank_id = request.form.get('bank_id')
    status = request.form.get('status')
    
    try:
        # Build query
        query = Cheque.query.join(Client).join(Branch).join(Bank)
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Cheque.due_date >= date_from_obj)
        
        if date_to:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Cheque.due_date <= date_to_obj)
        
        if bank_id:
            query = query.filter(Branch.bank_id == bank_id)
        
        if status:
            query = query.filter(Cheque.status == status)
        
        cheques = query.order_by(Cheque.due_date).all()
        
        if not cheques:
            flash('Aucun chèque trouvé avec les critères spécifiés.', 'warning')
            return redirect(url_for('exports.index'))
        
        # Generate Excel file
        excel_manager = ExcelManager()
        file_path = excel_manager.export_cheques(cheques, date_from, date_to)
        
        return send_file(file_path, as_attachment=True, download_name=f"export_cheques_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        
    except Exception as e:
        current_app.logger.error(f"Error exporting to Excel: {str(e)}")
        flash('Erreur lors de l\'export Excel.', 'danger')
        return redirect(url_for('exports.index'))

@exports_bp.route('/pdf', methods=['POST'])
@login_required
def export_pdf():
    # Get filter parameters
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    bank_id = request.form.get('bank_id')
    status = request.form.get('status')
    report_type = request.form.get('report_type', 'summary')
    
    try:
        # Build query
        query = Cheque.query.join(Client).join(Branch).join(Bank)
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Cheque.due_date >= date_from_obj)
        
        if date_to:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Cheque.due_date <= date_to_obj)
        
        if bank_id:
            query = query.filter(Branch.bank_id == bank_id)
        
        if status:
            query = query.filter(Cheque.status == status)
        
        cheques = query.order_by(Cheque.due_date).all()
        
        if not cheques:
            flash('Aucun chèque trouvé avec les critères spécifiés.', 'warning')
            return redirect(url_for('exports.index'))
        
        # Generate PDF file
        pdf_generator = PDFGenerator()
        file_path = pdf_generator.generate_report(cheques, report_type, {
            'date_from': date_from,
            'date_to': date_to,
            'bank_id': bank_id,
            'status': status
        })
        
        return send_file(file_path, as_attachment=True, download_name=f"rapport_cheques_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        
    except Exception as e:
        current_app.logger.error(f"Error exporting to PDF: {str(e)}")
        flash('Erreur lors de l\'export PDF.', 'danger')
        return redirect(url_for('exports.index'))

@exports_bp.route('/bordereau/<int:bank_id>')
@login_required
def bordereau(bank_id):
    """Generate deposit slip (bordereau de remise) for a specific bank"""
    bank = Bank.query.get_or_404(bank_id)
    
    # Get cheques ready for deposit
    cheques = Cheque.query.join(Branch).filter(
        Branch.bank_id == bank_id,
        Cheque.status == 'depose'
    ).order_by(Cheque.due_date).all()
    
    if not cheques:
        flash('Aucun chèque en dépôt pour cette banque.', 'warning')
        return redirect(url_for('exports.index'))
    
    try:
        # Generate bordereau PDF
        pdf_generator = PDFGenerator()
        file_path = pdf_generator.generate_bordereau(bank, cheques)
        
        return send_file(file_path, as_attachment=True, download_name=f"bordereau_{bank.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        
    except Exception as e:
        current_app.logger.error(f"Error generating bordereau: {str(e)}")
        flash('Erreur lors de la génération du bordereau.', 'danger')
        return redirect(url_for('exports.index'))
