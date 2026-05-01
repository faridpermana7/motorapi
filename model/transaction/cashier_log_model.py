from decimal import Decimal
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, Numeric
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import relationship
from ..base_model import Base

# CashierLog Item Entity (Database Model)
class CashierLogEntity(Base):
    __tablename__ = "cashier_logs"

    id = Column(Integer, primary_key=True, index=True) 
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    barcode = Column(String(50))
    action = Column(String(50)) 
    user_agent = Column(Text)
    device_info = Column(Text)
    location = Column(Text)

    created_at = Column(DateTime)
    created_by = Column(String)
 
    # ForeignKey
    transaction = relationship("TransactionEntity", back_populates="transaction_cashier_logs", foreign_keys=[transaction_id])

    # @property
    # def item_name(self) -> str:
    #     return self.item.name if self.item else None

# CashierLog Item DTO (API Model)
class CashierLogDTO(BaseModel):
    transaction_id: int
    barcode: str
    user_agent: str
    device_info: str
    location: str

class CashierLogResponseDTO(BaseModel):
    id: int
    transaction_id: int
    barcode: str
    user_agent: str
    device_info: str
    location: str

    created_at: Optional[datetime]
    created_by: Optional[str]

    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models
        json_encoders = {
            datetime: lambda v: (
                v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v.astimezone(timezone.utc)
            ).isoformat().replace("+00:00", "Z")
        }