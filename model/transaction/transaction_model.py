from decimal import Decimal
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Numeric
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
    customer_id = Column(Integer, ForeignKey("customers.id"))  
    payment_method = Column(String(50))
    discount = Column(Numeric(12, 2))
    tax_id = Column(Integer, ForeignKey("enum_tables.id"))
    tax_value = Column(Numeric(12, 2))
    total = Column(Numeric(12, 2))
    
    created_at = Column(DateTime)
    created_by = Column(String)
    updated_at = Column(DateTime)
    updated_by = Column(String)
    deleted_at = Column(DateTime)

    # Foreign-key constraints:
    customer = relationship("CustomerEntity", back_populates="customer_transactions", foreign_keys=[customer_id]) 
    tax = relationship("EnumTableEntity", back_populates="tax_transactions", foreign_keys=[tax_id])
    
    # Referenced by:
    transaction_cashier_logs = relationship(CashierLogEntity, back_populates="transaction", foreign_keys=[CashierLogEntity.transaction_id])
    transaction_transaction_items = relationship(TransactionItemEntity, back_populates="transaction", foreign_keys=[TransactionItemEntity.transaction_id])

    @property
    def customer_name(self) -> str:
        return self.customer.name if self.customer else None

    @property
    def tax_name(self) -> str:
        return self.tax.name if self.tax else None

# Transaction DTO (API Model)
class TransactionDTO(BaseModel):
    customer_id: int
    payment_method: str = "cash"
    discount: Decimal = Decimal("0.00")
    customer_id: int
    tax_id: int
    tax_value: Decimal = Decimal("0.00")
    total: Decimal = Decimal("0.00")


class TransactionResponseDTO(BaseModel):
    id: int
    customer_id: int
    payment_method: str = "cash"
    discount: Decimal = Decimal("0.00")
    customer_id: int
    tax_id: int
    tax_value: Decimal = Decimal("0.00")
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