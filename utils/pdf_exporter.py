"""
PDF Export functionality using ReportLab for professional document generation.
Optimized for offline desktop operations.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import logging
from typing import List, Dict

class PDFExporter:
    """Professional PDF exporter for cheque listings and reports"""
    
    def __init__(self):
        """Initialize PDF exporter with default settings"""
        self.page_size = A4
        self.margin = 1 * inch
        self.styles = getSampleStyleSheet()
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2C3E50')
        )
        
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#34495E')
        )
        
        logging.info("PDF Exporter initialized")
    
    def export_cheques_list(self, cheques_data: List[Dict], output_path: str, title: str = "Liste des Chèques") -> bool:
        """
        Export cheques to a formatted PDF list
        
        Args:
            cheques_data (list): List of cheque dictionaries
            output_path (str): Output file path
            title (str): Document title
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=self.page_size,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin
            )
            
            story = []
            
            # Add title
            story.append(Paragraph(title, self.title_style))
            story.append(Spacer(1, 20))
            
            # Add generation info
            generation_info = f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
            story.append(Paragraph(generation_info, self.subtitle_style))
            story.append(Spacer(1, 30))
            
            if not cheques_data:
                story.append(Paragraph("Aucun chèque trouvé.", self.styles['Normal']))
            else:
                # Prepare table data
                headers = [
                    'Date', 'Type', 'Numéro', 'Banque', 'Propriétaire', 
                    'Déposant', 'Montant', 'Échéance', 'Statut'
                ]
                
                # Calculate column widths dynamically to fit A4 page
                available_width = self.page_size[0] - (2 * self.margin)
                col_widths = [
                    available_width * 0.08,  # Date
                    available_width * 0.06,  # Type
                    available_width * 0.12,  # Numéro
                    available_width * 0.15,  # Banque
                    available_width * 0.18,  # Propriétaire
                    available_width * 0.18,  # Déposant
                    available_width * 0.10,  # Montant
                    available_width * 0.08,  # Échéance
                    available_width * 0.05   # Statut
                ]
                
                table_data = [headers]
                
                # Add cheque rows
                for cheque in cheques_data:
                    row = [
                        self._format_date(cheque.get('date_emission', '')),
                        cheque.get('type', 'CHQ'),
                        cheque.get('numero', ''),
                        self._truncate_text(cheque.get('banque', ''), 15),
                        self._truncate_text(cheque.get('proprietaire', ''), 20),
                        self._truncate_text(cheque.get('deposant', ''), 20),
                        f"{float(cheque.get('montant', 0)):,.2f}",
                        self._format_date(cheque.get('date_echeance', '')),
                        self._get_status_text(cheque.get('statut', ''))
                    ]
                    table_data.append(row)
                
                # Create table
                table = Table(table_data, colWidths=col_widths)
                
                # Table styling
                table.setStyle(TableStyle([
                    # Header row styling
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    
                    # Data rows styling
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('ALIGN', (6, 1), (6, -1), 'RIGHT'),  # Amount column right-aligned
                    
                    # Grid lines
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    
                    # Alternating row colors
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white]),
                    
                    # Padding
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ]))
                
                story.append(table)
                
                # Add summary
                story.append(Spacer(1, 30))
                total_amount = sum(float(cheque.get('montant', 0)) for cheque in cheques_data)
                summary_text = f"Total: {len(cheques_data)} chèques | Montant total: {total_amount:,.2f} MAD"
                summary_para = Paragraph(summary_text, self.subtitle_style)
                story.append(summary_para)
            
            # Build PDF
            doc.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
            
            logging.info(f"PDF exported successfully: {output_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error exporting PDF: {str(e)}")
            return False
    
    def export_summary_report(self, statistics: Dict, output_path: str) -> bool:
        """
        Export a summary statistics report
        
        Args:
            statistics (dict): Statistics data
            output_path (str): Output file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=self.page_size,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin
            )
            
            story = []
            
            # Title
            story.append(Paragraph("Rapport de Synthèse", self.title_style))
            story.append(Spacer(1, 20))
            
            # Generation date
            generation_info = f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
            story.append(Paragraph(generation_info, self.subtitle_style))
            story.append(Spacer(1, 30))
            
            # Statistics sections
            sections = [
                ("Statistiques Générales", self._format_general_stats(statistics)),
                ("Répartition par Type", self._format_type_stats(statistics)),
                ("Répartition par Statut", self._format_status_stats(statistics))
            ]
            
            for section_title, section_data in sections:
                if section_data:
                    # Section title
                    story.append(Paragraph(section_title, self.styles['Heading2']))
                    story.append(Spacer(1, 10))
                    
                    # Section table
                    table = Table(section_data)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.lightgrey, colors.white]),
                    ]))
                    
                    story.append(table)
                    story.append(Spacer(1, 30))
            
            # Build PDF
            doc.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
            
            logging.info(f"Summary report exported: {output_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error exporting summary report: {str(e)}")
            return False
    
    def _format_general_stats(self, stats: Dict) -> List[List[str]]:
        """Format general statistics for table display"""
        data = [
            ['Métrique', 'Valeur']
        ]
        
        general_metrics = [
            ('Nombre total de chèques', str(stats.get('total_count', 0))),
            ('Montant total', f"{stats.get('total_amount', 0):,.2f} MAD"),
            ('Montant moyen', f"{stats.get('average_amount', 0):,.2f} MAD"),
            ('Montant minimum', f"{stats.get('min_amount', 0):,.2f} MAD"),
            ('Montant maximum', f"{stats.get('max_amount', 0):,.2f} MAD"),
            ('Exports en attente', str(stats.get('pending_exports', 0))),
            ('Années avec données', str(stats.get('years_with_data', 0)))
        ]
        
        data.extend(general_metrics)
        return data
    
    def _format_type_stats(self, stats: Dict) -> List[List[str]]:
        """Format type statistics for table display"""
        type_counts = stats.get('count_by_type', {})
        if not type_counts:
            return None
        
        data = [['Type', 'Nombre']]
        for type_name, count in type_counts.items():
            data.append([type_name, str(count)])
        
        return data
    
    def _format_status_stats(self, stats: Dict) -> List[List[str]]:
        """Format status statistics for table display"""
        status_counts = stats.get('count_by_status', {})
        if not status_counts:
            return None
        
        data = [['Statut', 'Nombre']]
        for status, count in status_counts.items():
            status_text = self._get_status_text(status)
            data.append([status_text, str(count)])
        
        return data
    
    def _format_date(self, date_value) -> str:
        """Format date for display"""
        if not date_value:
            return ""
        
        if isinstance(date_value, str):
            try:
                # Try parsing different date formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                    try:
                        date_obj = datetime.strptime(date_value, fmt)
                        return date_obj.strftime('%d/%m/%Y')
                    except ValueError:
                        continue
                return date_value  # Return as-is if parsing fails
            except:
                return date_value
        
        return str(date_value)
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to fit in table cell"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    def _get_status_text(self, status: str) -> str:
        """Convert status code to readable text"""
        status_map = {
            'en_attente': 'EN ATTENTE',
            'encaisse': 'ENCAISSE',
            'rejete': 'REJETÉ',
            'impaye': 'IMPAYE',
            'depose': 'DÉPOSÉ',
            'annule': 'ANNULÉ'
        }
        return status_map.get(status.lower(), status.upper())
    
    def _add_page_number(self, canvas_obj, doc):
        """Add page number to PDF pages"""
        page_num = canvas_obj.getPageNumber()
        text = f"Page {page_num}"
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.drawRightString(
            doc.pagesize[0] - doc.rightMargin,
            doc.bottomMargin / 2,
            text
        )
    
    def export_bank_deposit_slip(self, cheques_data: List[Dict], bank_name: str, output_path: str) -> bool:
        """
        Export a bank deposit slip (bordereau de remise)
        
        Args:
            cheques_data (list): List of cheques for deposit
            bank_name (str): Bank name
            output_path (str): Output file path
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=self.page_size,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin
            )
            
            story = []
            
            # Title
            title = f"Bordereau de Remise - {bank_name}"
            story.append(Paragraph(title, self.title_style))
            story.append(Spacer(1, 20))
            
            # Date and info
            deposit_date = datetime.now().strftime('%d/%m/%Y')
            info_text = f"Date de dépôt: {deposit_date} | Nombre de chèques: {len(cheques_data)}"
            story.append(Paragraph(info_text, self.subtitle_style))
            story.append(Spacer(1, 30))
            
            # Cheques table
            headers = ['N°', 'Numéro de chèque', 'Montant', 'Date d\'échéance', 'Propriétaire']
            table_data = [headers]
            
            total_amount = 0
            for i, cheque in enumerate(cheques_data, 1):
                amount = float(cheque.get('montant', 0))
                total_amount += amount
                
                row = [
                    str(i),
                    cheque.get('numero', ''),
                    f"{amount:,.2f}",
                    self._format_date(cheque.get('date_echeance', '')),
                    self._truncate_text(cheque.get('proprietaire', ''), 25)
                ]
                table_data.append(row)
            
            # Add total row
            table_data.append(['', 'TOTAL', f"{total_amount:,.2f} MAD", '', ''])
            
            # Create table
            table = Table(table_data)
            table.setStyle(TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                
                # Total row styling
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E74C3C')),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                
                # General styling
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (2, 1), (2, -1), 'RIGHT'),  # Amount column
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.lightgrey, colors.white]),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            story.append(table)
            
            # Signature section
            story.append(Spacer(1, 50))
            signature_text = "Signature et cachet:"
            story.append(Paragraph(signature_text, self.styles['Normal']))
            
            # Build PDF
            doc.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
            
            logging.info(f"Bank deposit slip exported: {output_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error exporting deposit slip: {str(e)}")
            return False