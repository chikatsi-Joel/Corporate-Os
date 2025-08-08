from sqlalchemy.orm import Session
from app.database.models import ShareIssuance, User
from app.schemas.issuance import ShareIssuanceCreate, ShareIssuanceStatus, ShareIssuanceUpdate
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date, datetime
import os
from app.services.certificate_service import CertificateService
from sqlalchemy import func, and_
from bus_event.events.decorators import publish_event, EventType, publish_event_async


class IssuanceService:
    @staticmethod
    def get_issuance_by_id(db: Session, issuance_id: UUID) -> Optional[ShareIssuance]:
        return db.query(ShareIssuance).filter(ShareIssuance.id == issuance_id).first()
    
    @staticmethod
    def get_issuances(db: Session, skip: int = 0, limit: int = 100) -> List[ShareIssuance]:
        return db.query(ShareIssuance).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_issuances_by_id(db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[ShareIssuance]:
        return db.query(ShareIssuance).filter(ShareIssuance.id == user_id).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_issuances_by_shareholder(db: Session, shareholder_id: UUID, skip: int = 0, limit: int = 100) -> List[ShareIssuance]:
        return db.query(ShareIssuance).filter(ShareIssuance.shareholder_id == shareholder_id).offset(skip).limit(limit).all()
    
    @staticmethod
    @publish_event_async(EventType.SHARE_ISSUED, source="issuance_service")
    def create_issuance(db: Session, issuance: ShareIssuanceCreate) -> dict[str, str]:
        total_amount = issuance.shares_count * issuance.share_price
        
        # Créer l'émission
        db_issuance = ShareIssuance(
            shareholder_id=issuance.shareholder_id,
            number_of_shares=issuance.shares_count,
            price_per_share=issuance.share_price,
            total_amount=total_amount,
            issue_date=datetime.utcnow(),
            status=ShareIssuanceStatus.ISSUED.value
        )
        
        db.add(db_issuance)
        db.commit()
        db.refresh(db_issuance)
        
        # Générer le certificat PDF
        try:
            certificate_path = CertificateService.generate_certificate(db_issuance, db)
            db_issuance.certificate_path = certificate_path
            db.commit()
            db.refresh(db_issuance)
        except Exception as e:
            print(f"Erreur lors de la génération du certificat: {e}")
        
        return {
            "id": db_issuance.id,
            "shareholder_id": db_issuance.shareholder_id,
            "total_amount": db_issuance.total_amount,
            "certificate_path": db_issuance.certificate_path,
            "created_at": db_issuance.created_at,
            "updated_at": db_issuance.updated_at,
            "shares_count": db_issuance.number_of_shares,
            "share_price": db_issuance.price_per_share,
            "status": db_issuance.status
        }
    
    @staticmethod
    def update_issuance(db: Session, issuance_id: UUID, issuance_update: ShareIssuanceUpdate) -> Optional[ShareIssuance]:
        db_issuance = IssuanceService.get_issuance_by_id(db, issuance_id)
        if db_issuance:
            update_data = issuance_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_issuance, field, value)
            
            # Recalculer le montant total si nécessaire
            if 'number_of_shares' in update_data or 'price_per_share' in update_data:
                db_issuance.total_amount = db_issuance.number_of_shares * db_issuance.price_per_share
            
            db.commit()
            db.refresh(db_issuance)
        return db_issuance

    @staticmethod
    def get_shareholder_summary(db: Session, shareholder_id: UUID) -> dict:
        """Retourne un résumé des actions d'un actionnaire - Optimisé avec une seule requête"""
        result = db.query(
            func.coalesce(func.sum(ShareIssuance.number_of_shares), 0).label('total_shares'),
            func.coalesce(func.sum(ShareIssuance.total_amount), 0).label('total_value'),
            func.count(ShareIssuance.id).label('total_issuances')
        ).filter(ShareIssuance.shareholder_id == shareholder_id).first()
        
        return {
            'total_shares': int(result[0] or 0),
            'total_value': float(result[1] or 0),
            'total_issuances': int(result[2] or 0)
        }
    
    @staticmethod
    def get_cap_table_summary(db: Session) -> dict:
        """Retourne un résumé de la table de capitalisation - Optimisé avec une seule requête"""
        # Requête optimisée avec jointure et groupement
        shareholder_shares = db.query(
            User.username,
            User.first_name,
            User.last_name,
            func.coalesce(func.sum(ShareIssuance.number_of_shares), 0).label('shares'),
            func.coalesce(func.sum(ShareIssuance.total_amount), 0).label('value')
        ).outerjoin(ShareIssuance, and_(User.id == ShareIssuance.shareholder_id, User.user_type == 'actionnaire'))\
         .filter(User.user_type == 'actionnaire')\
         .group_by(User.id, User.username, User.first_name, User.last_name)\
         .all()
        
        # Calculer les totaux
        total_shares = sum(int(row[3]) for row in shareholder_shares)
        total_value = sum(float(row[4]) for row in shareholder_shares)
        
        # Préparer les données avec pourcentages
        shareholders_data = []
        for shareholder in shareholder_shares:
            percentage = (int(shareholder[3]) / total_shares * 100) if total_shares > 0 else 0
            shareholders_data.append({
                'username': shareholder[0],
                'first_name': shareholder[1],
                'last_name': shareholder[2],
                'shares': int(shareholder[3]),
                'value': float(shareholder[4]),
                'percentage': round(percentage, 2)
            })
        
        return {
            'total_shares': total_shares,
            'total_value': total_value,
            'shareholders': shareholders_data
        }
    
    @staticmethod
    def get_issuances_with_shareholder_info(db: Session, skip: int = 0, limit: int = 100, shareholder_id: Optional[UUID] = None) -> List[dict]:
        """Récupère les émissions avec les informations de l'actionnaire - Optimisé avec jointure"""
        query = db.query(ShareIssuance, User).join(User, ShareIssuance.shareholder_id == User.id)
        
        if shareholder_id:
            query = query.filter(ShareIssuance.shareholder_id == shareholder_id)
        
        results = query.offset(skip).limit(limit).all()
        
        issuances_data = []
        for issuance, shareholder in results:
            issuance_dict = {
                'id': issuance.id,
                'shareholder_id': issuance.shareholder_id,
                'number_of_shares': issuance.number_of_shares,
                'price_per_share': float(issuance.price_per_share),
                'total_amount': float(issuance.total_amount),
                'issue_date': issuance.issue_date,
                'status': issuance.status,
                'certificate_path': issuance.certificate_path,
                'created_at': issuance.created_at,
                'updated_at': issuance.updated_at,
                'shareholder': {
                    'id': shareholder.id,
                    'username': shareholder.username,
                    'first_name': shareholder.first_name,
                    'last_name': shareholder.last_name,
                    'email': shareholder.email
                }
            }
            issuances_data.append(issuance_dict)
        
        return issuances_data 