from typing import Optional, Dict, Any
from keycloak import KeycloakOpenID, KeycloakAdmin
from app.core.keycloak_config import keycloak_config
import logging

logger = logging.getLogger(__name__)

class KeycloakService:
    """Service pour gérer l'authentification et l'autorisation avec Keycloak"""
    
    def __init__(self):
        self.config = keycloak_config
        
        self.keycloak_openid = KeycloakOpenID(
            server_url=self.config.SERVER_URL,
            client_id=self.config.CLIENT_ID,
            realm_name=self.config.REALM,
            client_secret_key=self.config.CLIENT_SECRET,
            verify=True
        )
        
        try:
            self.keycloak_admin = KeycloakAdmin(
                server_url=self.config.SERVER_URL,
                username=self.config.ADMIN_USERNAME,
                password=self.config.ADMIN_PASSWORD,
                realm_name=self.config.REALM,
                verify=True
            )
        except Exception as e:
            logger.warning(f"Impossible de se connecter à Keycloak Admin: {e}")
            self.keycloak_admin = None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authentifier un utilisateur avec Keycloak"""
        try:
            token = self.keycloak_openid.token(
                username=username,
                password=password
            )
            return token
        except Exception as e:
            logger.error(f"Erreur d'authentification: {e}")
            return None
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Vérifier un token JWT"""
        try:
            token_info = self.keycloak_openid.decode_token(
                token,
                key=self.keycloak_openid.public_key(),
                options={
                    "verify_signature": True,
                    "verify_aud": False,
                    "verify_exp": True
                }
            )
            return token_info
        except Exception as e:
            logger.error(f"Erreur de vérification du token: {e}")
            return None
    
    def get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Obtenir les informations d'un utilisateur"""
        try:
            user_info = self.keycloak_openid.userinfo(token)
            return user_info
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos utilisateur: {e}")
            return None
    
    def get_user_roles(self, token: str) -> list:
        """Obtenir les rôles d'un utilisateur"""
        try:
            token_info = self.verify_token(token)
            if token_info and 'realm_access' in token_info:
                return token_info['realm_access'].get('roles', [])
            return []
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des rôles: {e}")
            return []
    
    def has_role(self, token: str, role: str) -> bool:
        """Vérifier si un utilisateur a un rôle spécifique"""
        roles = self.get_user_roles(token)
        return role in roles
    
    def is_admin(self, token: str) -> bool:
        """Vérifier si un utilisateur est admin"""
        return self.has_role(token, self.config.ADMIN_ROLE)
    
    def is_shareholder(self, token: str) -> bool:
        """Vérifier si un utilisateur est actionnaire"""
        return self.has_role(token, self.config.SHAREHOLDER_ROLE)
    
    def create_user(self, username: str, email: str, password: str, role: str) -> Optional[str]:
        """Créer un nouvel utilisateur dans Keycloak"""
        if not self.keycloak_admin:
            logger.error("Keycloak Admin non disponible")
            return None
        
        try:
            # Créer l'utilisateur
            user_id = self.keycloak_admin.create_user({
                "username": username,
                "email": email,
                "enabled": True,
                "credentials": [{
                    "type": "password",
                    "value": password,
                    "temporary": False
                }]
            })
            
            # Assigner le rôle
            role_id = self.keycloak_admin.get_realm_role(role)
            self.keycloak_admin.assign_realm_roles(user_id=user_id, roles=[role_id])
            
            return user_id
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'utilisateur: {e}")
            return None
    
    def update_user(self, user_id: str, **kwargs) -> bool:
        """Mettre à jour un utilisateur"""
        if not self.keycloak_admin:
            return False
        
        try:
            self.keycloak_admin.update_user(user_id=user_id, payload=kwargs)
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'utilisateur: {e}")
            return False
    
    def delete_user(self, user_id: str) -> bool:
        """Supprimer un utilisateur"""
        if not self.keycloak_admin:
            return False
        
        try:
            self.keycloak_admin.delete_user(user_id=user_id)
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'utilisateur: {e}")
            return False
    
    def get_users(self) -> list:
        """Obtenir la liste des utilisateurs"""
        if not self.keycloak_admin:
            return []
        
        try:
            return self.keycloak_admin.get_users()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des utilisateurs: {e}")
            return []
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Obtenir un utilisateur par son nom d'utilisateur"""
        if not self.keycloak_admin:
            return None
        
        try:
            users = self.keycloak_admin.get_users({"username": username})
            return users[0] if users else None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'utilisateur: {e}")
            return None


keycloak_service = KeycloakService() 