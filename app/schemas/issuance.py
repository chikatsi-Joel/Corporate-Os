from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal


class ShareIssuanceBase(BaseModel):
    """Schéma de base pour une émission d'actions"""
    shareholder_id: UUID = Field(..., description="Identifiant de l'actionnaire")
    shares_count: int = Field(..., description="Nombre d'actions émises", gt=0, example=100)
    share_price: Decimal = Field(..., description="Prix par action", gt=0, example=50.00)
    status: str = Field("issued", description="Statut de l'émission", example="issued", pattern="^(issued|pending|cancelled)$")


class ShareIssuanceCreate(ShareIssuanceBase):
    """Schéma pour la création d'une émission d'actions"""
    pass


class ShareIssuanceUpdate(BaseModel):
    """Schéma pour la mise à jour d'une émission d'actions"""
    shares_count: Optional[int] = Field(None, description="Nombre d'actions émises", gt=0, example=100)
    share_price: Optional[Decimal] = Field(None, description="Prix par action", gt=0, example=50.00)
    status: Optional[str] = Field(None, description="Statut de l'émission", example="issued", pattern="^(issued|pending|cancelled)$")


class ShareIssuance(ShareIssuanceBase):
    """Schéma complet d'une émission d'actions"""
    id: UUID = Field(..., description="Identifiant unique de l'émission")
    shareholder_id: UUID = Field(..., description="Identifiant de l'actionnaire")
    total_amount: Decimal = Field(..., description="Montant total de l'émission", example=50000.00)
    certificate_path: Optional[str] = Field(None, description="Chemin vers le certificat PDF", example="/certificates/issuance_123.pdf")
    created_at: datetime = Field(..., description="Date de création de l'émission")
    updated_at: datetime = Field(..., description="Date de dernière modification de l'émission")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "shareholder_id": "123e4567-e89b-12d3-a456-426614174001",
                "number_of_shares": 1000,
                "price_per_share": 50.00,
                "total_amount": 50000.00,
                "issue_date": "2024-01-01",
                "status": "issued",
                "certificate_path": "/certificates/issuance_123.pdf",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class ShareIssuanceWithShareholder(ShareIssuance):
    """Schéma d'une émission d'actions avec les informations de l'actionnaire"""
    shareholder: dict = Field(..., description="Informations de base de l'actionnaire")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "shareholder_id": "123e4567-e89b-12d3-a456-426614174001",
                "number_of_shares": 1000,
                "price_per_share": 50.00,
                "total_amount": 50000.00,
                "issue_date": "2024-01-01",
                "status": "issued",
                "certificate_path": "/certificates/issuance_123.pdf",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "shareholder": {
                    "id": "123e4567-e89b-12d3-a456-426614174001",
                    "username": "john.doe",
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com"
                }
            }
        } 