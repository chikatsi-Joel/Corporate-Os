from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    database_url: str = "postgresql://corporate_user:corporate_password@postgres:5432/corporate_os"
    
    # Configuration Keycloak avec valeurs par défaut pour Docker
    keycloak_url: str = "http://keycloak:8080"
    keycloak_realm: str = "corporate-os"
    keycloak_client_id: str = "corporate-os-client"
    keycloak_client_secret: str = "corporate-os-client-secret"
    keycloak_admin_username: str = "admin"
    keycloak_admin_password: str = "admin"
    keycloak_admin_client_id: str = "admin-cli"  
    
    # Configuration pour les tentatives de connexion Keycloak
    keycloak_connection_timeout: int = 30
    keycloak_retry_attempts: int = 3
    keycloak_retry_delay: int = 5
    
    # Configuration RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@rabbitmq:5672/"
    
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    app_name: str = "Corporate OS"
    app_version: str = "1.0.0"
    debug: bool = True
    
    certificates_dir: str = "certificates"
    uploads_dir: str = "uploads"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validation et correction de l'URL Keycloak
        if self.keycloak_url == "http://localhost:8080":
            # Si on est dans un conteneur Docker, utiliser le nom du service
            if os.getenv("DOCKER_ENV") or os.path.exists("/.dockerenv"):
                self.keycloak_url = "http://keycloak:8080"
            else:
                self.keycloak_url = "http://localhost:8080"


settings = Settings() 