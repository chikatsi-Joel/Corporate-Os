from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session
from app.database.models import ShareIssuance, User
from typing import Optional
import os
from datetime import datetime
from app.core.config import settings


class CertificateService:
    @staticmethod
    def generate_certificate(issuance: ShareIssuance, db: Session) -> str:
        """Génère un certificat PDF pour une émission d'actions"""
        
        # Créer le dossier certificates s'il n'existe pas
        os.makedirs(settings.certificates_dir, exist_ok=True)
        
        # Nom du fichier
        filename = f"certificate_{issuance.id}_{issuance.issue_date.strftime('%Y%m%d')}.pdf"
        filepath = os.path.join(settings.certificates_dir, filename)
        
        # Créer le document PDF
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Centré
        )
        
        normal_style = styles['Normal']
        normal_style.fontSize = 12
        normal_style.spaceAfter = 12
        
        # Titre
        title = Paragraph("CERTIFICAT D'ACTIONS", title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Informations de l'émission
        shareholder = db.query(User).filter(User.id == issuance.shareholder_id).first()
        
        # Tableau des informations
        data = [
            ['Numéro de certificat:', str(issuance.id)],
            ['Date d\'émission:', issuance.issue_date.strftime('%d/%m/%Y')],
            ['Actionnaire:', f"{shareholder.first_name} {shareholder.last_name}"],
            ['Email:', shareholder.email],
            ['Nombre d\'actions:', str(issuance.number_of_shares)],
            ['Prix par action:', f"{issuance.price_per_share:.2f} €"],
            ['Montant total:', f"{issuance.total_amount:.2f} €"],
            ['Statut:', issuance.status.upper()]
        ]
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # Texte légal
        legal_text = """
        <b>Déclarations importantes :</b><br/>
        Ce certificat atteste que l'actionnaire mentionné ci-dessus est propriétaire du nombre d'actions indiqué.
        Ce document est généré automatiquement par le système Corporate OS et constitue une preuve de propriété.
        <br/><br/>
        <b>Conditions :</b><br/>
        - Les actions sont soumises aux statuts de la société
        - Le transfert d'actions peut être soumis à des restrictions
        - Ce certificat doit être conservé précieusement
        """
        
        legal_paragraph = Paragraph(legal_text, normal_style)
        story.append(legal_paragraph)
        story.append(Spacer(1, 30))
        
        # Signature
        signature_text = """
        <b>Signature autorisée :</b><br/>
        ___________________________<br/>
        Date : """ + datetime.now().strftime('%d/%m/%Y')
        
        signature_paragraph = Paragraph(signature_text, normal_style)
        story.append(signature_paragraph)
        
        # Construire le PDF
        doc.build(story)
        
        # Ajouter un filigrane
        CertificateService._add_watermark(filepath)
        
        return filepath
    
    @staticmethod
    def _add_watermark(filepath: str):
        """Ajoute un filigrane au PDF"""
        try:
            # Ouvrir le PDF existant
            reader = open(filepath, 'rb')
            content = reader.read()
            reader.close()
            
            # Créer un nouveau PDF avec filigrane
            output = open(filepath + '.tmp', 'wb')
            output.write(content)
            output.close()
            
            # Ajouter le filigrane
            c = canvas.Canvas(filepath)
            c.setFont("Helvetica", 60)
            c.setFillAlpha(0.1)  # Transparence
            c.setFillColor(colors.red)
            c.rotate(45)
            c.drawString(200, 0, "CORPORATE OS")
            c.save()
            
            # Remplacer le fichier original
            os.rename(filepath + '.tmp', filepath)
            
        except Exception as e:
            print(f"Erreur lors de l'ajout du filigrane: {e}")
    
    @staticmethod
    def get_certificate_path(issuance_id: str) -> Optional[str]:
        """Retourne le chemin du certificat pour une émission donnée"""
        certificates_dir = settings.certificates_dir
        for filename in os.listdir(certificates_dir):
            if filename.startswith(f"certificate_{issuance_id}_"):
                return os.path.join(certificates_dir, filename)
        return None 