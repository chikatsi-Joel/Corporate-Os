from sqlalchemy import Column, String, Integer, DateTime, Text, Numeric, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base
import uuid


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keycloak_id = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
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
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    company_name = Column(String(255))
    address = Column(Text)
    phone = Column(String(50))
    tax_id = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relations
    user = relationship("User", back_populates="shareholder_profile")


class ShareIssuance(Base):
    __tablename__ = "share_issuances"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shareholder_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    number_of_shares = Column(Integer, nullable=False)
    price_per_share = Column(Numeric(10, 2), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    issue_date = Column(DateTime, nullable=False, index=True)
    certificate_path = Column(String(500))
    status = Column(String(50), default="issued", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relations
    shareholder = relationship("User", back_populates="share_issuances")
    
    __table_args__ = (
        CheckConstraint(number_of_shares > 0, name='positive_shares'),
        CheckConstraint(price_per_share >= 0, name='non_negative_price'),
        CheckConstraint(status.in_(['pending', 'issued', 'cancelled']), name='valid_status'),
    ) 