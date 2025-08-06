#!/usr/bin/env python3
"""
Script pour configurer automatiquement Keycloak
"""

import requests
import json
import time
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KeycloakSetup:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.admin_token = None
        
    def wait_for_keycloak(self, max_retries: int = 30):
        """Attendre que Keycloak soit prêt"""
        logger.info("Attente du démarrage de Keycloak...")
        for i in range(max_retries):
            try:
                response = requests.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    logger.info("Keycloak est prêt!")
                    return True
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(2)
            logger.info(f"Tentative {i+1}/{max_retries}...")
        
        logger.error("Keycloak n'est pas accessible")
        return False
    
    def get_admin_token(self, username: str = "admin", password: str = "admin") -> bool:
        """Obtenir le token d'administration"""
        try:
            response = requests.post(
                f"{self.base_url}/realms/master/protocol/openid-connect/token",
                data={
                    "username": username,
                    "password": password,
                    "grant_type": "password",
                    "client_id": "admin-cli"
                }
            )
            
            if response.status_code == 200:
                self.admin_token = response.json()["access_token"]
                logger.info("Token d'administration obtenu")
                return True
            else:
                logger.error(f"Erreur lors de l'obtention du token: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Erreur: {e}")
            return False
    
    def create_realm(self, realm_name: str = "actions-realm") -> bool:
        """Créer un nouveau realm"""
        try:
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
            
            realm_data = {
                "realm": realm_name,
                "enabled": True,
                "displayName": "Actions Management Realm"
            }
            
            response = requests.post(
                f"{self.base_url}/admin/realms",
                headers=headers,
                json=realm_data
            )
            
            if response.status_code == 201:
                logger.info(f"Realm '{realm_name}' créé")
                return True
            else:
                logger.error(f"Erreur lors de la création du realm: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Erreur: {e}")
            return False
    
    def create_client(self, realm_name: str, client_id: str = "actions-api") -> bool:
        """Créer un client pour l'API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
            
            client_data = {
                "clientId": client_id,
                "enabled": True,
                "publicClient": False,
                "standardFlowEnabled": True,
                "directAccessGrantsEnabled": True,
                "serviceAccountsEnabled": True,
                "authorizationServicesEnabled": True
            }
            
            response = requests.post(
                f"{self.base_url}/admin/realms/{realm_name}/clients",
                headers=headers,
                json=client_data
            )
            
            if response.status_code == 201:
                logger.info(f"Client '{client_id}' créé")
                return True
            else:
                logger.error(f"Erreur lors de la création du client: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Erreur: {e}")
            return False
    
    def create_roles(self, realm_name: str) -> bool:
        """Créer les rôles nécessaires"""
        try:
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
            
            roles = ["admin", "shareholder"]
            
            for role in roles:
                role_data = {
                    "name": role,
                    "description": f"Role {role} for actions management"
                }
                
                response = requests.post(
                    f"{self.base_url}/admin/realms/{realm_name}/roles",
                    headers=headers,
                    json=role_data
                )
                
                if response.status_code == 201:
                    logger.info(f"Rôle '{role}' créé")
                else:
                    logger.error(f"Erreur lors de la création du rôle '{role}': {response.status_code}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Erreur: {e}")
            return False
    
    def create_users(self, realm_name: str) -> bool:
        """Créer les utilisateurs par défaut"""
        try:
            headers = {
                "Authorization": f"Bearer {self.admin_token}",
                "Content-Type": "application/json"
            }
            
            users = [
                {
                    "username": "admin",
                    "email": "admin@example.com",
                    "firstName": "Admin",
                    "lastName": "User",
                    "enabled": True,
                    "credentials": [{
                        "type": "password",
                        "value": "admin123",
                        "temporary": False
                    }],
                    "realmRoles": ["admin"]
                },
                {
                    "username": "shareholder",
                    "email": "shareholder@example.com",
                    "firstName": "Shareholder",
                    "lastName": "User",
                    "enabled": True,
                    "credentials": [{
                        "type": "password",
                        "value": "shareholder123",
                        "temporary": False
                    }],
                    "realmRoles": ["shareholder"]
                }
            ]
            
            for user_data in users:
                response = requests.post(
                    f"{self.base_url}/admin/realms/{realm_name}/users",
                    headers=headers,
                    json=user_data
                )
                
                if response.status_code == 201:
                    logger.info(f"Utilisateur '{user_data['username']}' créé")
                else:
                    logger.error(f"Erreur lors de la création de l'utilisateur '{user_data['username']}': {response.status_code}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Erreur: {e}")
            return False
    
    def setup(self):
        """Configuration complète de Keycloak"""
        logger.info("Début de la configuration Keycloak...")
        
        if not self.wait_for_keycloak():
            return False
        
        if not self.get_admin_token():
            return False
        
        realm_name = "actions-realm"
        if not self.create_realm(realm_name):
            return False
        
        # Créer le client
        if not self.create_client(realm_name):
            return False
        
        # Créer les rôles
        if not self.create_roles(realm_name):
            return False
        
        # Créer les utilisateurs
        if not self.create_users(realm_name):
            return False
        
        logger.info("Configuration Keycloak terminée avec succès!")
        return True

def main():
    setup = KeycloakSetup()
    if setup.setup():
        print(" Configuration Keycloak réussie!")
        print(" Interface d'administration: http://localhost:8080")
        print(" Admin: admin / admin123")
        print(" Actionnaire: shareholder / shareholder123")
    else:
        print(" Échec de la configuration Keycloak")

if __name__ == "__main__":
    main() 