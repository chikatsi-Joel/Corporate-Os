from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    username: str = Field(..., description="Nom d'utilisateur unique", example="gweunshy@gmail.com")
    email: EmailStr = Field(..., description="Adresse email de l'utilisateur", example="gweunshy@gmail.com")
    first_name: Optional[str] = Field(None, description="Prénom de l'utilisateur", example="Gradi")
    last_name: Optional[str] = Field(None, description="Nom de famille de l'utilisateur", example="Joel")
    role: str = Field(..., description="Rôle de l'utilisateur", example="admin", pattern="^(admin|actionnaire)$")


class UserCreate(UserBase):
    """Schéma pour la création d'un utilisateur"""
    password: str = Field(..., description="Mot de passe de l'utilisateur", example="securepassword123")


class UserUpdate(BaseModel):
    """Schéma pour la mise à jour d'un utilisateur"""
    first_name: Optional[str] = Field(None, description="Prénom de l'utilisateur", example="Gradi")
    last_name: Optional[str] = Field(None, description="Nom de famille de l'utilisateur", example="Joel")
    email: Optional[EmailStr] = Field(None, description="Adresse email de l'utilisateur", example="gweunshy@gmail.com")


class User(UserBase):
    """Schéma complet d'un utilisateur"""
    id: UUID = Field(..., description="Identifiant unique de l'utilisateur")
    keycloak_id: str = Field(..., description="Identifiant Keycloak de l'utilisateur")
    created_at: datetime = Field(..., description="Date de création de l'utilisateur")
    updated_at: datetime = Field(..., description="Date de dernière modification de l'utilisateur")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "gweunshy@gmail.com",
                "email": "gweunshy@gmail.com",
                "first_name": "Gradi",
                "last_name": "Joel",
                "role": "admin",
                "keycloak_id": "keycloak-user-123",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class UserWithShares(User):
    """Schéma d'un utilisateur avec ses actions"""
    total_shares: int = Field(0, description="Nombre total d'actions détenues", example=1000)
    total_value: float = Field(0.0, description="Valeur totale des actions", example=50000.0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "gweunshy@gmail.com",
                "email": "gweunshy@gmail.com",
                "first_name": "Gradi",
                "last_name": "Joel",
                "role": "actionnaire",
                "keycloak_id": "keycloak-user-123",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "total_shares": 1000,
                "total_value": 50000.0
            }
        } 