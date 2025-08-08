import requests
import json
from typing import Optional, Dict, Any
from fastapi import HTTPException
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)

class KeycloakService:
    def __init__(self, 
                 server_url: str, 
                 realm_name: str, 
                 client_id: str, 
                 client_secret: str,
                 admin_username: str,
                 admin_password: str):
        self.server_url = server_url.rstrip('/')
        self.realm_name = realm_name
        self.client_id = client_id
        self.client_secret = client_secret
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.admin_token = None

    
    def get_admin_token(self) -> str:
        """Obtient un token d'administration pour Keycloak"""
        try:

            url = f"{self.server_url}/realms/master/protocol/openid-connect/token"
            
            payload = {
                'grant_type': 'password',
                'client_id': 'admin-cli',
                'username': self.admin_username,
                'password': self.admin_password
            }
            
            response = requests.post(url, data=payload)
            response.raise_for_status()
            
            token_data = response.json()
            self.admin_token = token_data['access_token']
            return self.admin_token
            
        except requests.RequestException as e:
            logger.error(f"Erreur lors de l'obtention du token admin: {e}")
            raise HTTPException(status_code=500, detail="Impossible d'obtenir le token admin")

    
    def create_user(self, username: str, email: str, password: str, first_name: str = None, last_name: str = None, role: str = None) -> Dict[str, Any]:
        """Crée un utilisateur dans Keycloak"""
        try:
            self.get_admin_token()
            
            url = f"{self.server_url}/admin/realms/{self.realm_name}/users"
            
            user_data = {
                "username": username,
                "email": email,
                "enabled": True,
                "emailVerified": True,
                "firstName": first_name or "",
                "lastName": last_name or "",
                "credentials": [
                    {
                        "type": "password",
                        "value": password,
                        "temporary": False
                    }
                ]
            }
            
            headers = {
                'Authorization': f'Bearer {self.admin_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, json=user_data, headers=headers)
            
            # Gérer les erreurs spécifiques
            if response.status_code == 409:
                raise HTTPException(status_code=409, detail="Utilisateur déjà existant")
            
            response.raise_for_status()
            
            location_header = response.headers.get('Location')
            if location_header:
                user_id = location_header.split('/')[-1]
            else:
                # Si pas d'en-tête Location, chercher l'utilisateur par username
                user_id = self._get_user_id_by_username(username)
                print(f"\n\nID utilisateur trouvé par nom d'utilisateur: {user_id}")
            
            # Assigner le rôle si spécifié
            if role and user_id:
                try:
                    print(f"\n\nID utilisateur trouvé par nom d'utilisateur: {user_id}")
                    self.assign_role_to_user(user_id, role)
                except Exception as e:
                    logger.warning(f"Erreur lors de l'assignation du rôle {role} à l'utilisateur {username}: {e}")
            
            return {"id": user_id, "username": username, "email": email}
            
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la création de l'utilisateur: {e}")
            if hasattr(e, 'response') and e.response:
                if e.response.status_code == 409:
                    raise HTTPException(status_code=409, detail="Utilisateur déjà existant")
                elif e.response.status_code == 401:
                    # Token expiré, renouveler et réessayer
                    self.admin_token = None
                    return self.create_user(username, email, password, first_name, last_name, role)
            raise HTTPException(status_code=500, detail=f"Impossible de créer l'utilisateur: {str(e)}")

    def _get_user_id_by_username(self, username: str) -> Optional[str]:
        """Récupère l'ID d'un utilisateur par son nom d'utilisateur"""
        try:
            if not self.admin_token:
                self.get_admin_token()
            
            url = f"{self.server_url}/admin/realms/{self.realm_name}/users"
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            params = {'username': username}
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            users = response.json()
            if users:
                return users[0].get('id')
            return None
            
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la recherche de l'utilisateur: {e}")
            return None

    
    def assign_role_to_user(self, user_id: str, role_name: str):
        """Assigne un rôle à un utilisateur"""
        try:
            if not self.admin_token:
                self.get_admin_token()
            
            # Récupérer le rôle
            headers = {
                'Authorization': f'Bearer {self.admin_token}',
                'Content-Type': 'application/json'
            }
        
            # Assigner le rôle à l'utilisateur
            assign_url = f"{self.server_url}/admin/realms/{self.realm_name}/users/{user_id}/role-mappings/realm"
            assign_response = requests.post(assign_url, json=[role_name], headers=headers)
            assign_response.raise_for_status()
            
        except requests.RequestException as e:
            logger.error(f"Erreur lors de l'assignation du rôle: {e}")
            # Ne pas lever d'exception car ce n'est pas critique

    
    def delete_user(self, user_id: str):
        """Supprime un utilisateur de Keycloak"""
        if not self.admin_token:
            self.get_admin_token()
        
        try:
            url = f"{self.server_url}/admin/realms/{self.realm_name}/users/{user_id}"
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Utilisateur {user_id} supprimé de Keycloak")
            
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la suppression de l'utilisateur: {e}")
            raise HTTPException(status_code=500, detail="Erreur lors de la suppression de l'utilisateur")



keycloak_service = KeycloakService(
    server_url=settings.keycloak_url,  
    realm_name=settings.keycloak_realm,    
    client_id=settings.keycloak_client_id,    
    client_secret=settings.keycloak_client_secret,
    admin_username=settings.keycloak_admin_username,       
    admin_password=settings.keycloak_admin_password  
)