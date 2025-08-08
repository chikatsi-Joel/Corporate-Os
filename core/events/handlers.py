"""
Handlers d'événements pour Corporate OS
"""

import logging
import json
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from decimal import Decimal
from .decorators import event_handler
from .models import Event, EventType

logger = logging.getLogger(__name__)


def convert_decimal_to_float(obj):
    """Convertit les objets Decimal en float pour la sérialisation JSON"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimal_to_float(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    else:
        return obj


@event_handler(EventType.USER_LOGIN)
def handle_user_login(event: Event):
    """Handler pour les événements de connexion utilisateur"""
    try:
        username = event.payload.get("username", "unknown")
        logger.info(f"Utilisateur connecté: {username}")
        
        return True
    except Exception as e:
        logger.error(f"Erreur dans handle_user_login: {e}")
        return False


@event_handler(EventType.SHARE_ISSUED)
def handle_share_issued(event: Event):
    """Handler pour les événements d'émission d'actions"""
    try:
        share_data = event.payload
        logger.info(f"Émission d'actions traitée: {share_data}")
        
        return True
    except Exception as e:
        logger.error(f"Erreur dans handle_share_issued: {e}")
        return False


@event_handler(EventType.CERTIFICATE_GENERATED)
def handle_certificate_generated(event: Event):
    """Handler pour les événements de génération de certificats"""
    try:
        certificate_data = event.payload
        logger.info(f"Certificat généré: {certificate_data}")
        
        return True
    except Exception as e:
        logger.error(f"Erreur dans handle_certificate_generated: {e}")
        return False


@event_handler(EventType.AUDIT_LOG, async_handler=True)
async def handle_audit_log(event: Event):
    """Handler asynchrone pour les événements d'audit"""
    try:
        audit_data = event.payload
        logger.info(f"Événement d'audit traité: {audit_data}")
    
        return True
    except Exception as e:
        logger.error(f"Erreur dans handle_audit_log: {e}")
        return False


@event_handler(EventType.SYSTEM_ERROR)
def handle_system_error(event: Event):
    """Handler pour les erreurs système"""
    try:
        error_data = event.payload
        logger.error(f"Erreur système détectée: {error_data}")
        
        return True
    except Exception as e:
        logger.error(f"Erreur dans handle_system_error: {e}")
        return False


@event_handler(EventType.AUDIT_LOG)
def handle_audit_persistence(event: Event):
    """Handler pour persister les événements d'audit en base de données"""
    try:
        from app.database.database import get_db
        from app.database.models import AuditEvent
        from sqlalchemy.orm import Session
        
        db = next(get_db())
        
        payload = event.payload
        metadata = event.metadata
        
        # Mapper les types d'événements vers les actions appropriées
        action_mapping = {
            EventType.USER_LOGIN.value: "login",
            EventType.USER_LOGOUT.value: "logout",
            EventType.SHAREHOLDER_CREATED.value: "create",
            EventType.SHAREHOLDER_UPDATED.value: "update",
            EventType.SHARE_ISSUED.value: "create",
            EventType.CERTIFICATE_GENERATED.value: "generate",
            EventType.SYSTEM_ERROR.value: "error",
            EventType.NOTIFICATION.value: "notification"
        }
        
        action = payload.get("action") or action_mapping.get(event.type.value, "unknown")
        
        # Convertir les objets Decimal en float pour la sérialisation JSON
        converted_payload = convert_decimal_to_float(payload)
        converted_metadata = convert_decimal_to_float(metadata) if metadata else None
        
        # Créer l'événement d'audit
        audit_event = AuditEvent(
            event_type=event.type.value,
            event_id=event.id,
            user_id=payload.get("user_id") or metadata.get("user_id") if metadata else None,
            user_email=payload.get("user_email") or metadata.get("user_email") if metadata else None,
            user_role=payload.get("user_role") or metadata.get("user_role") if metadata else None,
            resource_type=payload.get("resource_type") or metadata.get("resource_type") if metadata else None,
            resource_id=payload.get("resource_id") or metadata.get("resource_id") if metadata else None,
            action=action,
            description=payload.get("description") or metadata.get("description") if metadata else None,
            event_data=converted_payload,
            previous_data=convert_decimal_to_float(payload.get("previous_data")) if payload.get("previous_data") else None,
            processed_at=datetime.utcnow(),
            status="processed"
        )
        
        # Persister en base de données
        db.add(audit_event)
        db.commit()
        db.refresh(audit_event)
        
        logger.info(f"Événement d'audit persisté en base de données: {audit_event.id} (Type: {event.type.value}, Action: {action})")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la persistance de l'événement d'audit: {e}")
        return False
    finally:
        # Fermer la session
        if 'db' in locals():
            db.close()
