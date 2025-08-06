from fastapi import APIRouter, Depends, HTTPException, status
from app.services.keycloak_service import keycloak_service
from app.schemas.keycloak_auth import KeycloakLoginRequest, KeycloakTokenResponse
from app.api.deps import get_current_user
from typing import Dict, Any

router = APIRouter()

@router.post("/login", response_model=KeycloakTokenResponse)
def login_keycloak(login_data: KeycloakLoginRequest):
    token = keycloak_service.authenticate_user(
        username=login_data.username,
        password=login_data.password
    )
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    return KeycloakTokenResponse(
        access_token=token['access_token'],
        token_type=token['token_type'],
        expires_in=token['expires_in'],
        refresh_token=token.get('refresh_token'),
        scope=token.get('scope')
    )

@router.get("/me")
def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    return current_user 