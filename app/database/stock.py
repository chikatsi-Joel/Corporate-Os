import uuid
from enum import Enum
from sqlalchemy import Column, String, Enum as SqlEnum, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class Stock(Base):
    __tablename__ = "stocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shareholder_id = Column(UUID(as_uuid=True), ForeignKey("shareholders.user_id"))
    nombre = Column(Integer, nullable=False)
    date_emission = Column(DateTime, default=datetime.utcnow)
    certificat_path = Column(String)

    shareholder = relationship("Shareholder") 