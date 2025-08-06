from fastapi import APIRouter
from app.api.v1 import auth, users, stocks, certificates, keycloak_auth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(keycloak_auth.router, prefix="/keycloak", tags=["keycloak"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
api_router.include_router(certificates.router, prefix="/certificates", tags=["certificates"]) 