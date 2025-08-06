from ..crud.user_repository import *
from .keycloak_service import KeycloakService

class user_service :
    def __init__(self, db: Session):
        self.db = db
        self.keycloak = KeycloakService()
        
    def add_user(self, user : User) :
        self.keycloak.create_user(user.name, user.email, user.hashed_password,
                                  user.role)
        create_user(self.db, user=user)
        
        
    def get_user_by_email(self, email: str) :
        return get_user_by_email(self.db, email=email)
        