
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from keycloak import KeycloakOpenID
from app.core.config import settings


keycloak_openid = KeycloakOpenID(
    server_url=settings.keycloak_url,
    client_id=settings.keycloak_client_id,
    realm_name=settings.keycloak_realm,
    verify=True
)

security = HTTPBearer()

class permission:
    
    def hasPermission(role : str) :
        def decorator(func):
            def wrapper(*args, **kwargs):
                current_user = kwargs.get('current_user')
                if not current_user or current_user.role != role:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Accès refusé"
                    )
                return func(*args, **kwargs)
            return wrapper