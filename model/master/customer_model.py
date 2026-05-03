from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import relationship

from model.transaction.transaction_model import TransactionEntity

from ..base_model import Base

# Customer Entity (Database Model)
class CustomerEntity(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type_id = Column(Integer, ForeignKey("enum_tables.id")) 
    phone = Column(String(20))
    email = Column(String(100)) 
    address = Column(Text)
    created_at = Column(DateTime)
    created_by = Column(String)
    updated_at = Column(DateTime)
    updated_by = Column(String)
    deleted_at = Column(DateTime)
    
    # Foreign-key constraints:
    type = relationship("EnumTableEntity", back_populates="type_customers", foreign_keys=[type_id])

    # Referenced by:
    customer_transactions = relationship(TransactionEntity, back_populates="customer", foreign_keys=[TransactionEntity.customer_id])


    @property
    def type_name(self) -> str:
        return self.type.name if self.type else None

# Customer DTO (API Model)
class CustomerDTO(BaseModel):
    name: str
    type_id: int
    phone: str
    email: str
    address: str

class CustomerResponseDTO(BaseModel):
    id: int
    name: str
    type_id: int
    type_name: Optional[str] = None
    phone: str
    email: str
    address: str
    created_at: Optional[datetime]
    created_by: Optional[str] 
    updated_at: Optional[datetime]
    updated_by: Optional[str]
    deleted_at: Optional[datetime]

    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models
        json_encoders = {
            datetime: lambda v: (
                v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v.astimezone(timezone.utc)
            ).isoformat().replace("+00:00", "Z")
        }