from decimal import Decimal
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, Numeric
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import relationship

from model.transaction.transaction_item_model import TransactionItemEntity
from ..base_model import Base

from .cashier_log_model import CashierLogEntity

# Transaction Entity (Database Model)
class TransactionEntity(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True) 
    cashier_id = Column(Integer, ForeignKey("users.id"))  
    payment_method = Column(String(50))
    total = Column(Numeric(12, 2))
    
    created_at = Column(DateTime)
    created_by = Column(String)
    updated_at = Column(DateTime)
    updated_by = Column(String)
    deleted_at = Column(DateTime)

    # ForeignKey
    cashier = relationship("UserEntity", back_populates="user_transactions", foreign_keys=[cashier_id]) 
    
    # Relationship from others to this
    transaction_cashier_logs = relationship(CashierLogEntity, back_populates="transaction", foreign_keys=[CashierLogEntity.transaction_id])
    transaction_transaction_items = relationship(TransactionItemEntity, back_populates="transaction", foreign_keys=[TransactionItemEntity.transaction_id])

    @property
    def cashier_name(self) -> str:
        return self.cashier.name if self.cashier else None

# Transaction DTO (API Model)
class TransactionDTO(BaseModel):
    cashier_id: int
    payment_method: str

    name: Optional[str] = None
    code: Optional[str] = None
    barcode: Optional[str] = None
    brand: Optional[str] = None
    description: Optional[str] = None
    minimum_stock: int = 0
    stock: int = 0
    cost_price: Decimal = Decimal("0.00")
    selling_price: Decimal = Decimal("0.00")
    total: Decimal = Decimal("0.00")


class TransactionResponseDTO(BaseModel):
    id: int
    cashier_id: int
    payment_method: str
    total: Decimal = Decimal("0.00")
    
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