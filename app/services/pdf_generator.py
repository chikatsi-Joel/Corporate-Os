import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from app.core.config import settings
from app.database.stock import Stock
from app.database.users import User

class PDFGenerator:
    def __init__(self):
        self.certificates_dir = settings.CERTIFICATES_DIR
        os.makedirs(self.certificates_dir, exist_ok=True)
    
    def generate_certificate(self, stock: Stock, shareholder: User) -> str:
        """Génère un certificat PDF pour une action"""
        filename = f"certificate_{stock.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.certificates_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1
        )
        
        normal_style = styles['Normal']
        
        title = Paragraph("CERTIFICAT D'ACTIONS", title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        shareholder_info = [
            ["Nom:", shareholder.name],
            ["Email:", shareholder.email],
            ["Date d'émission:", stock.date_emission.strftime("%d/%m/%Y")],
            ["Nombre d'actions:", str(stock.nombre)],
            ["ID de l'action:", str(stock.id)]
        ]
        
        t = Table(shareholder_info, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(t)
        story.append(Spacer(1, 30))
        
        cert_text = f"""
        Ce certificat atteste que {shareholder.name} possède {stock.nombre} action(s) 
        émise(s) le {stock.date_emission.strftime("%d/%m/%Y")}.
        
        Ce document est généré automatiquement et constitue une preuve de propriété.
        """
        
        cert_paragraph = Paragraph(cert_text, normal_style)
        story.append(cert_paragraph)
        
        doc.build(story)
        
        self._add_watermark(filepath)
        
        return filepath
    
    def _add_watermark(self, filepath: str):
        """Ajoute un filigrane au PDF"""
        # Cette fonction peut être implémentée pour ajouter un filigrane
        # Pour l'instant, on laisse vide
        pass 