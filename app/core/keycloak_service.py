import requests
import json
from typing import Optional, Dict, Any
from fastapi import HTTPException
import logging
from .config import settings

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
            url = f"{self.server_url}/auth/realms/master/protocol/openid-connect/token"
            
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

    
    def create_user(self, 
                   username: str, 
                   email: str, 
                   password: str,
                   role: str,
                   first_name: Optional[str] = None,
                   last_name: Optional[str] = None,
                   enabled: bool = True,
                   email_verified: bool = False) -> Dict[str, Any]:
        """Crée un utilisateur dans Keycloak et lui assigne un rôle"""
        
        if not self.admin_token:
            self.get_admin_token()
        
        try:
            # 1. Créer l'utilisateur
            user_data = {
                "username": username,
                "email": email,
                "emailVerified": email_verified,
                "enabled": enabled,
                "firstName": first_name,
                "lastName": last_name,
                "credentials": [
                    {
                        "type": "password",
                        "value": password,
                        "temporary": False
                    }
                ]
            }
            
            url = f"{self.server_url}/auth/admin/realms/{self.realm_name}/users"
            headers = {
                'Authorization': f'Bearer {self.admin_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, json=user_data, headers=headers)

            print(f"Response status code: {response}")  # Debugging line
            
            if response.status_code == 409:
                raise HTTPException(status_code=409, detail="Utilisateur déjà existant")
            
            response.raise_for_status()
            
            # 2. Récupérer l'ID de l'utilisateur créé
            user_id = self.get_user_by_username(username)['id']
            
            # 3. Assigner le rôle à l'utilisateur
            try:
                self.assign_role_to_user(user_id, role)
                logger.info(f"Rôle '{role}' assigné avec succès à l'utilisateur {username}")
            except Exception as role_error:
                logger.warning(f"Erreur lors de l'assignation du rôle '{role}' à l'utilisateur {username}: {role_error}")
                # L'utilisateur est créé mais sans le rôle - on peut choisir de continuer ou de lever une exception
            
            logger.info(f"Utilisateur {username} créé avec succès dans Keycloak")
            
            return {
                "id": user_id,
                "username": username,
                "email": email,
                "role": role,
                "message": "Utilisateur créé avec succès"
            }
            
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la création de l'utilisateur: {e}")
            if e.response and e.response.status_code == 401:
                # Token expiré, renouveler et réessayer
                self.get_admin_token()
                return self.create_user(username, email, password, role, first_name, last_name, enabled, email_verified)
            raise HTTPException(status_code=500, detail="Erreur lors de la création de l'utilisateur")
        
        
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Récupère un utilisateur par son nom d'utilisateur"""
        
        if not self.admin_token:
            self.get_admin_token()
        
        try:
            url = f"{self.server_url}/auth/admin/realms/{self.realm_name}/users"
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            params = {'username': username}
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            users = response.json()
            if users:
                return users[0]  # Retourne le premier utilisateur trouvé
            return None
            
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la recherche de l'utilisateur: {e}")
            return None

    def assign_role_to_user(self, user_id: str, role_name: str):
        """Assigne un rôle à un utilisateur"""
        
        if not self.admin_token:
            self.get_admin_token()
        
        try:
            # 1. Obtenir les détails du rôle
            role_url = f"{self.server_url}/auth/admin/realms/{self.realm_name}/roles/{role_name}"
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            
            role_response = requests.get(role_url, headers=headers)
            role_response.raise_for_status()
            role_data = role_response.json()
            
            # 2. Assigner le rôle à l'utilisateur
            assign_url = f"{self.server_url}/auth/admin/realms/{self.realm_name}/users/{user_id}/role-mappings/realm"
            role_mapping = [role_data]
            
            response = requests.post(assign_url, json=role_mapping, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Rôle {role_name} assigné à l'utilisateur {user_id}")
            
        except requests.RequestException as e:
            logger.error(f"Erreur lors de l'assignation du rôle: {e}")
            raise HTTPException(status_code=500, detail="Erreur lors de l'assignation du rôle")

    def delete_user(self, user_id: str):
        """Supprime un utilisateur de Keycloak"""
        
        if not self.admin_token:
            self.get_admin_token()
        
        try:
            url = f"{self.server_url}/auth/admin/realms/{self.realm_name}/users/{user_id}"
            headers = {'Authorization': f'Bearer {self.admin_token}'}
            
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Utilisateur {user_id} supprimé de Keycloak")
            
        except requests.RequestException as e:
            logger.error(f"Erreur lors de la suppression de l'utilisateur: {e}")
            raise HTTPException(status_code=500, detail="Erreur lors de la suppression de l'utilisateur")



keycloak_service = KeycloakService(
    server_url=settings.keycloak_url,  # URL de votre serveur Keycloak
    realm_name=settings.keycloak_realm,           # Nom de votre realm
    client_id=settings.keycloak_client_id,        # ID de votre client
    client_secret=settings.keycloak_client_secret,
    admin_username=settings.keycloak_admin_username,            # Nom d'utilisateur admin
    admin_password=settings.keycloak_admin_password    # Mot de passe admin
)