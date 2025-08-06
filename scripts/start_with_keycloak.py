#!/usr/bin/env python3
"""
Script de démarrage complet avec Keycloak
"""

import subprocess
import time
import requests
import logging
import os
import sys
from pathlib import Path

# Ajouter le répertoire racine au path Python
sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DockerComposeManager:
    def __init__(self):
        self.compose_file = "docker-compose.yml"
        
    def start_services(self):
        """Démarrer tous les services avec Docker Compose"""
        logger.info("🚀 Démarrage des services avec Docker Compose...")
        
        try:
            # Arrêter les services existants
            subprocess.run(["docker-compose", "down"], check=True)
            
            # Démarrer les services
            result = subprocess.run(
                ["docker-compose", "up", "-d"],
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("✅ Services démarrés avec succès!")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erreur lors du démarrage des services: {e}")
            logger.error(f"Sortie d'erreur: {e.stderr}")
            return False
    
    def wait_for_service(self, service_name: str, url: str, max_retries: int = 60):
        """Attendre qu'un service soit prêt"""
        logger.info(f"⏳ Attente du service {service_name}...")
        
        for i in range(max_retries):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"✅ {service_name} est prêt!")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
            if (i + 1) % 10 == 0:
                logger.info(f"   Tentative {i+1}/{max_retries}...")
        
        logger.error(f"❌ {service_name} n'est pas accessible après {max_retries} tentatives")
        return False
    
    def get_service_logs(self, service_name: str):
        """Obtenir les logs d'un service"""
        try:
            result = subprocess.run(
                ["docker-compose", "logs", service_name],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return "Impossible de récupérer les logs"

class KeycloakSetup:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.admin_token = None
        
    def wait_for_keycloak(self, max_retries: int = 60):
        """Attendre que Keycloak soit prêt"""
        logger.info("⏳ Attente du démarrage de Keycloak...")
        
        for i in range(max_retries):
            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                if response.status_code == 200:
                    logger.info("✅ Keycloak est prêt!")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
            if (i + 1) % 10 == 0:
                logger.info(f"   Tentative {i+1}/{max_retries}...")
        
        logger.error("❌ Keycloak n'est pas accessible")
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
                },
                timeout=10
            )
            
            if response.status_code == 200:
                self.admin_token = response.json()["access_token"]
                logger.info("✅ Token d'administration obtenu")
                return True
            else:
                logger.error(f"❌ Erreur lors de l'obtention du token: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
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
                json=realm_data,
                timeout=10
            )
            
            if response.status_code == 201:
                logger.info(f"✅ Realm '{realm_name}' créé")
                return True
            else:
                logger.error(f"❌ Erreur lors de la création du realm: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
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
                json=client_data,
                timeout=10
            )
            
            if response.status_code == 201:
                logger.info(f"✅ Client '{client_id}' créé")
                return True
            else:
                logger.error(f"❌ Erreur lors de la création du client: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
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
                    json=role_data,
                    timeout=10
                )
                
                if response.status_code == 201:
                    logger.info(f"✅ Rôle '{role}' créé")
                else:
                    logger.error(f"❌ Erreur lors de la création du rôle '{role}': {response.status_code}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
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
                    json=user_data,
                    timeout=10
                )
                
                if response.status_code == 201:
                    logger.info(f"✅ Utilisateur '{user_data['username']}' créé")
                else:
                    logger.error(f"❌ Erreur lors de la création de l'utilisateur '{user_data['username']}': {response.status_code}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            return False
    
    def setup(self):
        """Configuration complète de Keycloak"""
        logger.info("🔧 Début de la configuration Keycloak...")
        
        # Attendre que Keycloak soit prêt
        if not self.wait_for_keycloak():
            return False
        
        # Obtenir le token d'administration
        if not self.get_admin_token():
            return False
        
        # Créer le realm
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
        
        logger.info("✅ Configuration Keycloak terminée avec succès!")
        return True

def main():
    """Fonction principale"""
    print("🚀 Démarrage complet de l'application avec Keycloak")
    print("=" * 60)
    
    # Vérifier que Docker est disponible
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker n'est pas installé ou n'est pas accessible")
        return
    
    # Vérifier que Docker Compose est disponible
    try:
        subprocess.run(["docker-compose", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker Compose n'est pas installé ou n'est pas accessible")
        return
    
    # Démarrer les services
    docker_manager = DockerComposeManager()
    if not docker_manager.start_services():
        print("❌ Échec du démarrage des services")
        return
    
    # Attendre que les services soient prêts
    print("\n⏳ Attente que les services soient prêts...")
    
    # Attendre Keycloak
    if not docker_manager.wait_for_service("keycloak", "http://localhost:8080/health"):
        print("❌ Keycloak n'est pas accessible")
        print("📋 Logs Keycloak:")
        print(docker_manager.get_service_logs("keycloak"))
        return
    
    # Attendre l'application
    if not docker_manager.wait_for_service("app", "http://localhost:8000/health"):
        print("⚠️  L'application n'est pas encore prête, mais Keycloak est accessible")
    
    # Configurer Keycloak
    print("\n🔧 Configuration automatique de Keycloak...")
    keycloak_setup = KeycloakSetup()
    if not keycloak_setup.setup():
        print("❌ Échec de la configuration Keycloak")
        return
    
    # Afficher les informations finales
    print("\n" + "=" * 60)
    print("🎉 Configuration terminée avec succès!")
    print("\n📋 Informations d'accès:")
    print("🌐 Interface Keycloak: http://localhost:8080")
    print("   - Utilisateur: admin")
    print("   - Mot de passe: admin")
    print("\n🚀 Application: http://localhost:8000")
    print("📚 Documentation API: http://localhost:8000/docs")
    print("\n👤 Utilisateurs par défaut:")
    print("   - Admin: admin / admin123")
    print("   - Actionnaire: shareholder / shareholder123")
    print("\n🔧 Commandes utiles:")
    print("   - Voir les logs: docker-compose logs -f")
    print("   - Arrêter: docker-compose down")
    print("   - Redémarrer: docker-compose restart")
    print("=" * 60)

if __name__ == "__main__":
    main() 