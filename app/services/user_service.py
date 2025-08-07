from sqlalchemy.orm import Session
from app.database.models import User
from app.schemas.user import UserCreate, UserUpdate
from typing import List, Optional, Dict, Tuple
from uuid import UUID
from sqlalchemy import func


class UserService:
    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_keycloak_id(db: Session, keycloak_id: str) -> Optional[User]:
        return db.query(User).filter(User.keycloak_id == keycloak_id).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return db.query(User).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_shareholders(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return db.query(User).filter(User.role == 'actionnaire').offset(skip).limit(limit).all()
    
    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        db_user = User(**user.dict())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def update_user(db: Session, user_id: UUID, user_update: UserUpdate) -> Optional[User]:
        db_user = UserService.get_user_by_id(db, user_id)
        if db_user:
            update_data = user_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_user, field, value)
            db.commit()
            db.refresh(db_user)
        return db_user
    
    @staticmethod
    def delete_user(db: Session, user_id: UUID) -> bool:
        db_user = UserService.get_user_by_id(db, user_id)
        if db_user:
            db.delete(db_user)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_user_with_shares(db: Session, user_id: UUID) -> Optional[dict]:
        """Retourne un utilisateur avec le total de ses actions - Optimisé avec une seule requête"""
        from app.database.models import ShareIssuance
        
        result = db.query(
            User,
            func.coalesce(func.sum(ShareIssuance.number_of_shares), 0).label('total_shares'),
            func.coalesce(func.sum(ShareIssuance.total_amount), 0).label('total_value')
        ).outerjoin(ShareIssuance, User.id == ShareIssuance.shareholder_id).filter(User.id == user_id).group_by(User.id).first()
        
        if result:
            user_dict = {
                'id': result[0].id,
                'username': result[0].username,
                'email': result[0].email,
                'first_name': result[0].first_name,
                'last_name': result[0].last_name,
                'role': result[0].role,
                'total_shares': int(result[1]),
                'total_value': float(result[2])
            }
            return user_dict
        return None
    
    @staticmethod
    def get_shareholders_with_shares(db: Session, skip: int = 0, limit: int = 100) -> List[dict]:
        """Récupère tous les actionnaires avec leurs actions - Optimisé avec une seule requête"""
        from app.database.models import ShareIssuance
        
        results = db.query(
            User,
            func.coalesce(func.sum(ShareIssuance.number_of_shares), 0).label('total_shares'),
            func.coalesce(func.sum(ShareIssuance.total_amount), 0).label('total_value')
        ).outerjoin(ShareIssuance, User.id == ShareIssuance.shareholder_id)\
         .filter(User.role == 'actionnaire').group_by(User.id).offset(skip).limit(limit).all()
        
        shareholders_data = []
        for result in results:
            user_dict = {
                'id': result[0].id,
                'username': result[0].username,
                'email': result[0].email,
                'first_name': result[0].first_name,
                'last_name': result[0].last_name,
                'role': result[0].role,
                'total_shares': int(result[1]),
                'total_value': float(result[2])
            }
            shareholders_data.append(user_dict)
        
        return shareholders_data
    
    @staticmethod
    def get_shareholder_summary(db: Session, shareholder_id: UUID) -> Optional[dict]:
        """Retourne un résumé détaillé des actions d'un actionnaire"""
        from app.database.models import ShareIssuance
        
        result = db.query(
            func.coalesce(func.sum(ShareIssuance.number_of_shares), 0).label('total_shares'),
            func.coalesce(func.sum(ShareIssuance.total_amount), 0).label('total_value'),
            func.count(ShareIssuance.id).label('issuances_count'),
            func.max(ShareIssuance.issue_date).label('last_issuance_date')
        ).filter(ShareIssuance.shareholder_id == shareholder_id).first()
        
        if result:
            # Calculer le pourcentage de participation (nécessite le total global)
            total_global = db.query(func.sum(ShareIssuance.number_of_shares)).scalar() or 0
            percentage = (int(result[0]) / total_global * 100) if total_global > 0 else 0
            
            return {
                'shareholder_id': shareholder_id,
                'total_shares': int(result[0]),
                'total_value': float(result[1]),
                'percentage': round(percentage, 2),
                'issuances_count': int(result[2]),
                'last_issuance_date': result[3].isoformat() if result[3] else None
            }
        return None 