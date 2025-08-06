import uuid
from enum import Enum
from sqlalchemy import Column, String, Enum as SqlEnum, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class Shareholder(Base):
    __tablename__ = "shareholders"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    user = relationship("User", back_populates="shareholder")
