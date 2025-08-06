from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class KeycloakConfig(BaseModel):
    """Configuration pour Keycloak"""
    
    SERVER_URL: str = os.getenv("KEYCLOAK_SERVER_URL", "http://localhost:8080")
    
    REALM: str = os.getenv("KEYCLOAK_REALM", "actions-realm")
    
    CLIENT_ID: str = os.getenv("KEYCLOAK_CLIENT_ID", "actions-api")
    CLIENT_SECRET: str = os.getenv("KEYCLOAK_CLIENT_SECRET", "")
    
    ADMIN_USERNAME: str = os.getenv("KEYCLOAK_ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin")
    
    ADMIN_ROLE: str = "admin"
    SHAREHOLDER_ROLE: str = "shareholder"
    
    TOKEN_EXPIRE_MINUTES: int = int(os.getenv("KEYCLOAK_TOKEN_EXPIRE_MINUTES", "30"))
    
    LOGIN_REDIRECT_URL: str = os.getenv("KEYCLOAK_LOGIN_REDIRECT_URL", "http://localhost:3000/callback")
    LOGOUT_REDIRECT_URL: str = os.getenv("KEYCLOAK_LOGOUT_REDIRECT_URL", "http://localhost:3000")

keycloak_config = KeycloakConfig() 