# audit_system/models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()


class AuditEvent(Base):
    """Modèle pour stocker les événements d'audit"""
    __tablename__ = "audit_events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Identifiants de l'événement
    event_type = Column(String(50), nullable=False, index=True)
    event_id = Column(String(100), unique=True, nullable=False)  # UUID de l'événement
    
    # Contexte utilisateur
    user_id = Column(Integer, nullable=True, index=True)
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
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    processed_at = Column(DateTime, nullable=True)     # Quand l'audit a été traité
    
    # Statut
    status = Column(String(20), default="processed", nullable=False)  # processed, failed, pending
    
    __table_args__ = (
        Index('idx_event_user_date', 'event_type', 'user_id', 'created_at'),
        Index('idx_resource_date', 'resource_type', 'resource_id', 'created_at'),
        Index('idx_user_date', 'user_id', 'created_at'),
        Index('idx_date_type', 'created_at', 'event_type'),
    )
    
    def __repr__(self):
        return f"<AuditEvent(id={self.id}, type={self.event_type}, user={self.user_email}, action={self.action})>"
