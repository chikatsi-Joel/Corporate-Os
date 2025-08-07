from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal


class ShareIssuanceBase(BaseModel):
    number_of_shares: int = Field(gt=0, description="Nombre d'actions à émettre", example=1000)
    price_per_share: Decimal = Field(ge=0, description="Prix par action en euros", example=50.00)
    issue_date: date = Field(..., description="Date d'émission des actions", example="2024-01-01")
    status: str = Field("issued", description="Statut de l'émission", example="issued", regex="^(issued|pending|cancelled)$")


class ShareIssuanceCreate(ShareIssuanceBase):
    """Schéma pour la création d'une émission d'actions"""
    shareholder_id: UUID = Field(..., description="Identifiant de l'actionnaire")


class ShareIssuanceUpdate(BaseModel):
    """Schéma pour la mise à jour d'une émission d'actions"""
    number_of_shares: Optional[int] = Field(None, gt=0, description="Nombre d'actions à émettre", example=1000)
    price_per_share: Optional[Decimal] = Field(None, ge=0, description="Prix par action en euros", example=50.00)
    issue_date: Optional[date] = Field(None, description="Date d'émission des actions", example="2024-01-01")
    status: Optional[str] = Field(None, description="Statut de l'émission", example="issued", regex="^(issued|pending|cancelled)$")


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