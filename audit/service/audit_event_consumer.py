# audit_system/consumers.py
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from audit_system import AuditEvent
import logging
import json

logger = logging.getLogger(__name__)


class AuditEventConsumer:
    """Consumer pour traiter et analyser les événements d'audit"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        
    def get_events(
        self,
        event_types: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "created_at",
        order_direction: str = "desc"
    ) -> List[AuditEvent]:
        """
        Récupère les événements d'audit selon les critères spécifiés
        """
        query = self.db.query(AuditEvent)
        
        if event_types:
            query = query.filter(AuditEvent.event_type.in_(event_types))
        
        if user_id:
            query = query.filter(AuditEvent.user_id == user_id)
            
        if user_email:
            query = query.filter(AuditEvent.user_email == user_email)
        
        if resource_type:
            query = query.filter(AuditEvent.resource_type == resource_type)
            
        if resource_id:
            query = query.filter(AuditEvent.resource_id == resource_id)
        
        if action:
            query = query.filter(AuditEvent.action == action)
            
        if status:
            query = query.filter(AuditEvent.status == status)
        
        if start_date:
            query = query.filter(AuditEvent.created_at >= start_date)
            
        if end_date:
            query = query.filter(AuditEvent.created_at <= end_date)
        
        order_column = getattr(AuditEvent, order_by, AuditEvent.created_at)
        if order_direction.lower() == "asc":
            query = query.order_by(asc(order_column))
        else:
            query = query.order_by(desc(order_column))
        
        return query.offset(offset).limit(limit).all()
    
    
    def get_event_by_id(self, event_id: str) -> Optional[AuditEvent]:
        """Récupère un événement par son ID unique"""
        return self.db.query(AuditEvent).filter(AuditEvent.event_id == event_id).first()
    
    def get_user_activity(
        self,
        user_id: int,
        days: int = 30,
        actions: Optional[List[str]] = None
    ) -> List[AuditEvent]:
        """Récupère l'activité d'un utilisateur sur une période donnée"""
        start_date = datetime.now() - timedelta(days=days)
        
        query = self.db.query(AuditEvent).filter(
            and_(
                AuditEvent.user_id == user_id,
                AuditEvent.created_at >= start_date
            )
        )
        
        if actions:
            query = query.filter(AuditEvent.action.in_(actions))
        
        return query.order_by(desc(AuditEvent.created_at)).all()
    
    def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        include_views: bool = False
    ) -> List[AuditEvent]:
        """Récupère l'historique complet d'une ressource"""
        query = self.db.query(AuditEvent).filter(
            and_(
                AuditEvent.resource_type == resource_type,
                AuditEvent.resource_id == resource_id
            )
        )
        
        if not include_views:
            query = query.filter(AuditEvent.action != "view")
        
        return query.order_by(asc(AuditEvent.created_at)).all()
    
    def get_activity_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "event_type"
    ) -> Dict[str, int]:
        """
        Génère des statistiques d'activité
        group_by peut être: event_type, action, resource_type, user_id, status
        """
        query = self.db.query(AuditEvent)
        
        if start_date:
            query = query.filter(AuditEvent.created_at >= start_date)
        if end_date:
            query = query.filter(AuditEvent.created_at <= end_date)
        
        # Groupement et comptage
        group_column = getattr(AuditEvent, group_by, AuditEvent.event_type)
        results = query.with_entities(
            group_column,
            func.count(AuditEvent.id).label('count')
        ).group_by(group_column).all()
        
        return {str(result[0]): result[1] for result in results}
    
    def get_daily_activity(
        self,
        days: int = 30,
        event_types: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """Récupère l'activité quotidienne sur une période"""
        start_date = datetime.now() - timedelta(days=days)
        
        query = self.db.query(AuditEvent).filter(AuditEvent.created_at >= start_date)
        
        if event_types:
            query = query.filter(AuditEvent.event_type.in_(event_types))
        
        results = query.with_entities(
            func.date(AuditEvent.created_at).label('date'),
            func.count(AuditEvent.id).label('count')
        ).group_by(func.date(AuditEvent.created_at)).all()
        
        return {str(result[0]): result[1] for result in results}
    
    def get_top_users(
        self,
        limit: int = 10,
        days: int = 30,
        exclude_views: bool = True
    ) -> List[Dict[str, Any]]:
        """Récupère les utilisateurs les plus actifs"""
        start_date = datetime.now() - timedelta(days=days)
        
        query = self.db.query(AuditEvent).filter(
            and_(
                AuditEvent.created_at >= start_date,
                AuditEvent.user_id.isnot(None)
            )
        )
        
        if exclude_views:
            query = query.filter(AuditEvent.action != "view")
        
        results = query.with_entities(
            AuditEvent.user_id,
            AuditEvent.user_email,
            func.count(AuditEvent.id).label('activity_count')
        ).group_by(
            AuditEvent.user_id,
            AuditEvent.user_email
        ).order_by(
            desc(func.count(AuditEvent.id))
        ).limit(limit).all()
        
        return [
            {
                "user_id": result[0],
                "user_email": result[1],
                "activity_count": result[2]
            }
            for result in results
        ]
    
    def search_events(
        self,
        search_term: str,
        fields: Optional[List[str]] = None,
        **kwargs
    ) -> List[AuditEvent]:
        """
        Recherche dans les événements d'audit
        fields peut contenir: description, event_data, user_email, action
        """
        if not fields:
            fields = ["description", "user_email", "action"]
        
        conditions = []
        
        for field in fields:
            if hasattr(AuditEvent, field):
                column = getattr(AuditEvent, field)
                if field == "event_data":
                    conditions.append(
                        func.cast(column, str).contains(search_term)
                    )
                else:
                    conditions.append(column.contains(search_term))
        
        query = self.db.query(AuditEvent).filter(or_(*conditions))
        
        # Appliquer les autres filtres
        return self._apply_filters(query, **kwargs).all()
    
    def get_failed_events(self, limit: int = 100) -> List[AuditEvent]:
        """Récupère les événements en échec"""
        return self.db.query(AuditEvent).filter(
            AuditEvent.status == "failed"
        ).order_by(desc(AuditEvent.created_at)).limit(limit).all()
    
    def mark_as_processed(self, event_ids: List[str]) -> int:
        """Marque des événements comme traités"""
        updated = self.db.query(AuditEvent).filter(
            AuditEvent.event_id.in_(event_ids)
        ).update({
            "status": "processed",
            "processed_at": datetime.now()
        }, synchronize_session=False)
        
        self.db.commit()
        return updated
    
    def delete_old_events(self, days: int = 365) -> int:
        """Supprime les anciens événements d'audit"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        deleted = self.db.query(AuditEvent).filter(
            AuditEvent.created_at < cutoff_date
        ).delete(synchronize_session=False)
        
        self.db.commit()
        logger.info(f"Supprimé {deleted} événements d'audit antérieurs au {cutoff_date}")
        return deleted
    
    def process_events_batch(
        self,
        processor_func: Callable[[List[AuditEvent]], None],
        batch_size: int = 1000,
        status: str = "pending"
    ):
        """
        Traite les événements par lots avec une fonction personnalisée
        """
        offset = 0
        
        while True:
            events = self.db.query(AuditEvent).filter(
                AuditEvent.status == status
            ).offset(offset).limit(batch_size).all()
            
            if not events:
                break
            
            try:
                processor_func(events)
                
                # Marquer comme traités
                event_ids = [event.event_id for event in events]
                self.mark_as_processed(event_ids)
                
                logger.info(f"Traité un lot de {len(events)} événements")
                
            except Exception as e:
                logger.error(f"Erreur lors du traitement du lot: {e}")
                # Marquer comme échoués
                self.db.query(AuditEvent).filter(
                    AuditEvent.event_id.in_([event.event_id for event in events])
                ).update({"status": "failed"}, synchronize_session=False)
                self.db.commit()
            
            offset += batch_size
    
    def _apply_filters(self, query, **kwargs):
        """Applique les filtres communs à une requête"""
        for key, value in kwargs.items():
            if value is not None and hasattr(AuditEvent, key):
                if isinstance(value, list):
                    query = query.filter(getattr(AuditEvent, key).in_(value))
                else:
                    query = query.filter(getattr(AuditEvent, key) == value)
        
        return query
    
    def export_events_to_dict(self, events: List[AuditEvent]) -> List[Dict[str, Any]]:
        """Convertit une liste d'événements en dictionnaires pour l'export"""
        return [
            {
                "id": event.id,
                "event_type": event.event_type,
                "event_id": event.event_id,
                "user_id": event.user_id,
                "user_email": event.user_email,
                "user_role": event.user_role,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
                "action": event.action,
                "description": event.description,
                "event_data": event.event_data,
                "previous_data": event.previous_data,
                "created_at": event.created_at.isoformat() if event.created_at else None,
                "processed_at": event.processed_at.isoformat() if event.processed_at else None,
                "status": event.status
            }
            for event in events
        ]