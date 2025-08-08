# audit_system/services.py
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy import update, delete, and_, or_, desc, asc, func
from audit.service.audit_system import AuditEvent


class AuditEventError(Exception):
    pass


class AuditEventService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_event(self, event_data: dict) -> AuditEvent:
        """Crée un événement d'audit"""
        if 'event_id' not in event_data:
            event_data['event_id'] = str(uuid4())
        
        event = AuditEvent(**event_data)
        self.db.add(event)
        
        try:
            await self.db.commit()
            await self.db.refresh(event)
            return event
        except IntegrityError as e:
            await self.db.rollback()
            raise AuditEventError(f"Création échouée: {e}")

    async def get_by_id(self, event_id: int) -> Optional[AuditEvent]:
        """Récupère un événement par ID"""
        result = await self.db.execute(
            select(AuditEvent).where(AuditEvent.id == event_id)
        )
        return result.scalar_one_or_none()

    async def get_by_uuid(self, event_uuid: str) -> Optional[AuditEvent]:
        """Récupère un événement par UUID"""
        result = await self.db.execute(
            select(AuditEvent).where(AuditEvent.event_id == event_uuid)
        )
        return result.scalar_one_or_none()

    async def get_events(
        self,
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "created_at",
        order_desc: bool = True
    ) -> List[AuditEvent]:
        """Récupère les événements avec filtrage et pagination"""
        query = select(AuditEvent)
        
        # Filtres
        if filters:
            conditions = []
            for key, value in filters.items():
                if hasattr(AuditEvent, key) and value is not None:
                    if isinstance(value, list):
                        conditions.append(getattr(AuditEvent, key).in_(value))
                    else:
                        conditions.append(getattr(AuditEvent, key) == value)
            if conditions:
                query = query.where(and_(*conditions))
        
        # Tri
        order_col = getattr(AuditEvent, order_by, AuditEvent.created_at)
        query = query.order_by(desc(order_col) if order_desc else asc(order_col))
        
        # Pagination
        result = await self.db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_user_activity(self, user_id: int, days: int = 30) -> List[AuditEvent]:
        """Activité d'un utilisateur"""
        start_date = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            select(AuditEvent)
            .where(and_(
                AuditEvent.user_id == user_id,
                AuditEvent.created_at >= start_date
            ))
            .order_by(desc(AuditEvent.created_at))
        )
        return list(result.scalars().all())

    async def get_resource_history(self, resource_type: str, resource_id: str) -> List[AuditEvent]:
        """Historique d'une ressource"""
        result = await self.db.execute(
            select(AuditEvent)
            .where(and_(
                AuditEvent.resource_type == resource_type,
                AuditEvent.resource_id == resource_id
            ))
            .order_by(asc(AuditEvent.created_at))
        )
        return list(result.scalars().all())

    async def update_event(self, event_id: int, update_data: dict) -> Optional[AuditEvent]:
        """Met à jour un événement"""
        event = await self.get_by_id(event_id)
        if not event:
            return None
        
        for key, value in update_data.items():
            if hasattr(event, key):
                setattr(event, key, value)
        
        try:
            await self.db.commit()
            await self.db.refresh(event)
            return event
        except IntegrityError as e:
            await self.db.rollback()
            raise AuditEventError(f"Mise à jour échouée: {e}")

    async def bulk_update_status(self, event_ids: List[int], status: str) -> int:
        """Met à jour le statut en lot"""
        result = await self.db.execute(
            update(AuditEvent)
            .where(AuditEvent.id.in_(event_ids))
            .values(status=status, processed_at=datetime.utcnow())
        )
        await self.db.commit()
        return result.rowcount

    async def delete_event(self, event_id: int) -> bool:
        """Supprime un événement"""
        result = await self.db.execute(
            delete(AuditEvent).where(AuditEvent.id == event_id)
        )
        await self.db.commit()
        return result.rowcount > 0


    async def get_stats(self, group_by: str = "event_type") -> Dict[str, int]:
        """Statistiques d'activité"""
        group_col = getattr(AuditEvent, group_by, AuditEvent.event_type)
        result = await self.db.execute(
            select(group_col, func.count(AuditEvent.id))
            .group_by(group_col)
        )
        return {str(row[0]): row[1] for row in result}

    async def search_events(self, search_term: str, limit: int = 100) -> List[AuditEvent]:
        """Recherche textuelle"""
        result = await self.db.execute(
            select(AuditEvent)
            .where(or_(
                AuditEvent.description.ilike(f"%{search_term}%"),
                AuditEvent.user_email.ilike(f"%{search_term}%"),
                AuditEvent.action.ilike(f"%{search_term}%")
            ))
            .order_by(desc(AuditEvent.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())