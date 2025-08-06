from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.crud.stock_repository import get_stock
from app.crud.user_repository import get_user
from app.services.pdf_generator import PDFGenerator
from app.api.deps import get_current_user, get_current_admin
from app.core.role import Role
import os

router = APIRouter()
pdf_generator = PDFGenerator()

@router.get("/generate/{stock_id}")
def generate_certificate(
    stock_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    stock = get_stock(db, stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    if current_user.role == Role.ACTIONNAIRE and stock.shareholder_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    shareholder = get_user(db, stock.shareholder_id)
    if not shareholder:
        raise HTTPException(status_code=404, detail="Shareholder not found")
    
    try:
        certificate_path = pdf_generator.generate_certificate(stock, shareholder)
        
        stock.certificat_path = certificate_path
        db.commit()
        
        return {"message": "Certificat généré avec succès", "certificate_path": certificate_path}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération du certificat: {str(e)}"
        )

@router.get("/download/{stock_id}")
def download_certificate(
    stock_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Télécharge un certificat PDF"""
    stock = get_stock(db, stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    if current_user.role == Role.ACTIONNAIRE and stock.shareholder_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    if not stock.certificat_path or not os.path.exists(stock.certificat_path):
        raise HTTPException(
            status_code=404,
            detail="Certificat non trouvé. Veuillez d'abord le générer."
        )
    
    return FileResponse(
        stock.certificat_path,
        media_type='application/pdf',
        filename=f"certificate_{stock_id}.pdf"
    ) 