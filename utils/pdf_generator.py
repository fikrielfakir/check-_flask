from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import tempfile

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center
        )
        
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            alignment=1  # Center
        )
    
    def generate_report(self, cheques, report_type='summary', filters=None):
        """Generate PDF report for cheques"""
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        
        doc = SimpleDocTemplate(temp_file.name, pagesize=A4)
        story = []
        
        # Title
        title = "Rapport des Chèques"
        if filters and filters.get('status'):
            title += f" - {filters['status'].upper()}"
        
        story.append(Paragraph(title, self.title_style))
        
        # Date range
        if filters and (filters.get('date_from') or filters.get('date_to')):
            date_info = "Période: "
            if filters.get('date_from'):
                date_info += f"du {filters['date_from']} "
            if filters.get('date_to'):
                date_info += f"au {filters['date_to']}"
            story.append(Paragraph(date_info, self.subtitle_style))
        
        story.append(Spacer(1, 20))
        
        if report_type == 'summary':
            self._add_summary_section(story, cheques)
        else:
            self._add_detailed_section(story, cheques)
        
        doc.build(story)
        return temp_file.name
    
    def _add_summary_section(self, story, cheques):
        """Add summary statistics section"""
        # Calculate statistics
        total_amount = sum(float(cheque.amount) for cheque in cheques)
        status_counts = {}
        status_amounts = {}
        
        for cheque in cheques:
            status = cheque.status_text
            status_counts[status] = status_counts.get(status, 0) + 1
            status_amounts[status] = status_amounts.get(status, 0) + float(cheque.amount)
        
        # Summary table
        summary_data = [
            ['Statistiques Générales', ''],
            ['Nombre total de chèques', str(len(cheques))],
            ['Montant total', f"{total_amount:,.2f} MAD"],
        ]
        
        # Add status breakdown
        summary_data.append(['', ''])
        summary_data.append(['Répartition par statut', ''])
        
        for status, count in status_counts.items():
            amount = status_amounts[status]
            summary_data.append([f"{status}", f"{count} chèques - {amount:,.2f} MAD"])
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 30))
        
        # Detailed list
        self._add_cheque_table(story, cheques)
    
    def _add_detailed_section(self, story, cheques):
        """Add detailed cheques section"""
        self._add_cheque_table(story, cheques)
    
    def _add_cheque_table(self, story, cheques):
        """Add table with cheque details"""
        # Table headers
        headers = ['N°', 'Client', 'Banque', 'Montant', 'Échéance', 'Statut']
        data = [headers]
        
        # Add cheque data
        for cheque in cheques:
            row = [
                cheque.cheque_number or 'N/A',
                cheque.client.name[:30] + '...' if len(cheque.client.name) > 30 else cheque.client.name,
                cheque.branch.bank.name,
                f"{float(cheque.amount):,.2f}",
                cheque.due_date.strftime('%d/%m/%Y'),
                cheque.status_text
            ]
            data.append(row)
        
        # Create table
        table = Table(data, colWidths=[0.8*inch, 2.2*inch, 1.5*inch, 1*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Body styling
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            
            # Amount column alignment
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
        ]))
        
        story.append(Paragraph("Détail des Chèques", self.subtitle_style))
        story.append(table)
    
    def generate_bordereau(self, bank, cheques):
        """Generate deposit slip (bordereau de remise)"""
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.close()
        
        doc = SimpleDocTemplate(temp_file.name, pagesize=A4)
        story = []
        
        # Title
        story.append(Paragraph(f"BORDEREAU DE REMISE DE CHÈQUES", self.title_style))
        story.append(Paragraph(f"Banque: {bank.name}", self.subtitle_style))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%d/%m/%Y')}", self.styles['Normal']))
        story.append(Spacer(1, 30))
        
        # Cheques table
        headers = ['N°', 'Client', 'Montant', 'Échéance']
        data = [headers]
        
        total_amount = 0
        for idx, cheque in enumerate(cheques, 1):
            row = [
                str(idx),
                cheque.client.name,
                f"{float(cheque.amount):,.2f} MAD",
                cheque.due_date.strftime('%d/%m/%Y')
            ]
            data.append(row)
            total_amount += float(cheque.amount)
        
        # Add total row
        data.append(['', 'TOTAL', f"{total_amount:,.2f} MAD", ''])
        
        table = Table(data, colWidths=[0.5*inch, 3*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Body styling
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            
            # Total row styling
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            
            # Amount column alignment
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 50))
        
        # Signature section
        signature_data = [
            ['Déposé par:', 'Reçu par:'],
            ['', ''],
            ['Signature:', 'Signature:'],
            ['', ''],
            ['Date:', 'Date:']
        ]
        
        signature_table = Table(signature_data, colWidths=[3*inch, 3*inch])
        signature_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
        ]))
        
        story.append(signature_table)
        
        doc.build(story)
        return temp_file.name
