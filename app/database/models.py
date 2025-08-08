from sqlalchemy import Column, String, Integer, DateTime, Text, Numeric, ForeignKey, CheckConstraint, Boolean, Enum, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base
import uuid
import enum


class NotificationType(str, enum.Enum):
    """Types de notifications disponibles"""
    SHARE_ISSUANCE = "share_issuance"
    SHARE_TRANSFER = "share_transfer"
    CERTIFICATE_GENERATED = "certificate_generated"
    SYSTEM_ALERT = "system_alert"
    USER_REGISTRATION = "user_registration"
    CAP_TABLE_UPDATE = "cap_table_update"


class NotificationStatus(str, enum.Enum):
    """Statuts des notifications"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    READ = "read"


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keycloak_id = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relations
    shareholder_profile = relationship("ShareholderProfile", back_populates="user", uselist=False)
    share_issuances = relationship("ShareIssuance", back_populates="shareholder")
    
    __table_args__ = (
        CheckConstraint(role.in_(['admin', 'actionnaire']), name='valid_role'),
    )


class ShareholderProfile(Base):
    __tablename__ = "shareholder_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_name = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    tax_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relations
    user = relationship("User", back_populates="shareholder_profile")


class ShareIssuance(Base):
    __tablename__ = "share_issuances"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shareholder_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    number_of_shares = Column(Integer, nullable=False, index=True)
    price_per_share = Column(Numeric(10, 2), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    issue_date = Column(DateTime, nullable=False, index=True)
    certificate_path = Column(String(500), nullable=True)
    status = Column(String(50), default="issued", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relations
    shareholder = relationship("User", back_populates="share_issuances")
    
    __table_args__ = (
        CheckConstraint(number_of_shares > 0, name='positive_shares'),
        CheckConstraint(price_per_share >= 0, name='non_negative_price'),
        CheckConstraint(status.in_(['pending', 'issued', 'cancelled']), name='valid_status'),
    )


class AuditEvent(Base):
    """Modèle pour stocker les événements d'audit"""
    __tablename__ = "audit_events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Identifiants de l'événement
    event_type = Column(String(50), nullable=False, index=True)
    event_id = Column(String(100), unique=True, nullable=False)  # UUID de l'événement
    
    # Contexte utilisateur
    user_id = Column(String(255), nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    user_role = Column(String(50), nullable=True)
    
    # Contexte de l'action
    resource_type = Column(String(50), nullable=True)  # shareholder, share_issuance, etc.
    resource_id = Column(String(100), nullable=True)   # ID de la ressource concernée
    
    # Détails de l'événement
    action = Column(String(100), nullable=False)       # create, update, delete, view, etc.
    description = Column(Text, nullable=True)
    
    event_data = Column(JSON, nullable=True)           # Données spécifiques à l'événement
    previous_data = Column(JSON, nullable=True)        # État précédent (pour les updates)
    
    # Horodatage
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)     # Quand l'audit a été traité
    
    # Statut
    status = Column(String(20), default="processed", nullable=False)  # processed, failed, pending
    
    __table_args__ = (

        Index('idx_event_user_date', 'event_type', 'user_id', 'created_at'),
        Index('idx_resource_date', 'resource_type', 'resource_id', 'created_at'),
        Index('idx_user_date', 'user_id', 'created_at'),
        Index('idx_date_type', 'created_at', 'event_type'),
    )
