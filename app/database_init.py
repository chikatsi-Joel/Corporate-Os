import logging
from sqlalchemy.orm import Session
from app.db.session import engine
from app.db.session import SessionLocal
from app.crud.user_repository import create_user, get_user_by_email
from app.schemas.user import UserCreate
from app.core.role import Role
from app.database import users, stock, admin, shareholder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def init_db() -> None:
    db = SessionLocal()
    try:
        users.Base.metadata.create_all(bind=engine)
        stock.Base.metadata.create_all(bind=engine)
        admin.Base.metadata.create_all(bind=engine)
        shareholder.Base.metadata.create_all(bind=engine)
        
        user = get_user_by_email(db, email="admin@example.com")
        if not user:
            user_in = UserCreate(
                name="Administrateur",
                email="admin@example.com",
                password="admin123",
                role=Role.ADMIN
            )
            user = create_user(db=db, user=user_in)
            logger.info(f"Utilisateur admin créé: {user.email}")
        else:
            logger.info(f"Utilisateur admin existe déjà: {user.email}")
        
        shareholder_user = get_user_by_email(db, email="actionnaire@example.com")
        if not shareholder_user:
            shareholder_in = UserCreate(
                name="Actionnaire Test",
                email="actionnaire@example.com",
                password="actionnaire123",
                role=Role.ACTIONNAIRE
            )
            shareholder_user = create_user(db=db, user=shareholder_in)
            logger.info(f"Actionnaire de test créé: {shareholder_user.email}")
        else:
            logger.info(f"Actionnaire de test existe déjà: {shareholder_user.email}")
            
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {e}")
    finally:
        db.close()

def main() -> None:
    logger.info("Création des tables de base de données...")
    init_db()
    logger.info("Initialisation de la base de données terminée.")

if __name__ == "__main__":
    main() 