from decimal import Decimal
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, Numeric
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import relationship
from ..base_model import Base

# Transaction Item Entity (Database Model)
class TransactionItemEntity(Base):
    __tablename__ = "transaction_items"

    id = Column(Integer, primary_key=True, index=True) 
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    quantity = Column(Integer)
    price = Column(Numeric(12, 2))
    sub_total = Column(Numeric(12, 2))
    
    created_at = Column(DateTime)
    created_by = Column(String)
    updated_at = Column(DateTime)
    updated_by = Column(String)
    deleted_at = Column(DateTime)
 
    # Foreign-key constraints:
    item = relationship("ItemEntity", back_populates="item_transaction_items", foreign_keys=[item_id])
    transaction = relationship("TransactionEntity", back_populates="transaction_transaction_items", foreign_keys=[transaction_id])

    @property
    def item_name(self) -> str:
        return self.item.name if self.item else None

# Transaction Item DTO (API Model)
class TransactionItemDTO(BaseModel):
    transaction_id: int
    item_id: int
    quantity: int
    price: Decimal = Decimal("0.00")
    sub_total: Decimal = Decimal("0.00") 

class TransactionItemResponseDTO(BaseModel):
    id: int
    transaction_id: int
    item_id: int
    quantity: int
    price: Decimal = Decimal("0.00")
    sub_total: Decimal = Decimal("0.00")

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