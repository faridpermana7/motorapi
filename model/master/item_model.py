from decimal import Decimal
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, Numeric
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import relationship
from ..base_model import Base

# Item Entity (Database Model)
class ItemEntity(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True) 
    code = Column(String(50))
    barcode = Column(String(50))
    name = Column(String(255))
    brand = Column(String(100))
    description = Column(Text)
    uom_id = Column(Integer, ForeignKey("enum_tables.id")) 
    minimum_stock = Column(Integer) 
    cost_price = Column(Numeric(12, 2))
    selling_price = Column(Numeric(12, 2))
    stock = Column(Integer) 
    category_id = Column(Integer, ForeignKey("enum_tables.id")) 
    created_at = Column(DateTime)
    created_by = Column(String)
    updated_at = Column(DateTime)
    updated_by = Column(String)
    deleted_at = Column(DateTime)

    uom = relationship("EnumTableEntity", back_populates="uom_items", foreign_keys=[uom_id])
    category = relationship("EnumTableEntity", back_populates="category_items", foreign_keys=[category_id])

    @property
    def uom_name(self) -> str:
        return self.uom.name if self.uom else None

    @property
    def category_name(self) -> str:
        return self.category.name if self.category else None


# Item DTO (API Model)
class ItemDTO(BaseModel):
    uom_id: int
    category_id: int
     
    name: Optional[str] = None
    code: Optional[str] = None
    barcode: Optional[str] = None
    brand: Optional[str] = None
    description: Optional[str] = None
    minimum_stock: int = 0
    stock: int = 0
    cost_price: Decimal = Decimal("0.00")
    selling_price: Decimal = Decimal("0.00")


class ItemResponseDTO(BaseModel):
    id: int
    uom_id: int
    category_id: int
    uom_name: Optional[str] = None
    category_name: Optional[str] = None
 
    name: Optional[str] = None
    code: Optional[str] = None
    barcode: Optional[str] = None
    brand: Optional[str] = None
    description: Optional[str] = None
    minimum_stock: int = 0
    stock: int = 0
    cost_price: Decimal = Decimal("0.00")
    selling_price: Decimal = Decimal("0.00")

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