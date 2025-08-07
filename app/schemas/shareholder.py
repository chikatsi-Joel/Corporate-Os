from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class ShareholderProfileBase(BaseModel):
    company_name: Optional[str] = Field(None, description="Nom de l'entreprise de l'actionnaire", example="Acme Corp")
    address: Optional[str] = Field(None, description="Adresse de l'actionnaire", example="123 Main St, City, Country")
    phone: Optional[str] = Field(None, description="Numéro de téléphone de l'actionnaire", example="+1-555-123-4567")
    tax_id: Optional[str] = Field(None, description="Numéro d'identification fiscale", example="TAX123456789")


class ShareholderProfileCreate(ShareholderProfileBase):
    """Schéma pour la création d'un profil d'actionnaire"""
    user_id: UUID = Field(..., description="Identifiant de l'utilisateur associé")


class ShareholderProfileUpdate(ShareholderProfileBase):
    """Schéma pour la mise à jour d'un profil d'actionnaire"""
    pass


class ShareholderProfile(ShareholderProfileBase):
    """Schéma complet d'un profil d'actionnaire"""
    id: UUID = Field(..., description="Identifiant unique du profil")
    user_id: UUID = Field(..., description="Identifiant de l'utilisateur associé")
    created_at: datetime = Field(..., description="Date de création du profil")
    updated_at: datetime = Field(..., description="Date de dernière modification du profil")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "company_name": "Acme Corp",
                "address": "123 Main St, City, Country",
                "phone": "+1-555-123-4567",
                "tax_id": "TAX123456789",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        } 