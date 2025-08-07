from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    database_url: str = "postgresql://corporate_user:corporate_password@postgres:5432/corporate_os"
    
    keycloak_url: str = "http://keycloak:8080"
    keycloak_realm: str = "corporate-os"
    keycloak_client_id: str = "corporate-os-client"
    keycloak_admin_username: str = "admin"
    keycloak_admin_password: str = "admin"
    
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


settings = Settings() 