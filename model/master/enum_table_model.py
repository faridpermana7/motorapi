from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import relationship

from ..base_model import Base
from .item_model import ItemEntity

# Enum Table Entity (Database Model)
class EnumTableEntity(Base):
    __tablename__ = "enum_tables"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime)
    created_by = Column(String)
    updated_at = Column(DateTime)
    updated_by = Column(String)
    deleted_at = Column(DateTime)
    
    uom_items = relationship(ItemEntity, back_populates="uom", foreign_keys=[ItemEntity.uom_id])
    category_items = relationship(ItemEntity, back_populates="category", foreign_keys=[ItemEntity.category_id])

# Enum Table DTO (API Model)
class EnumTableDTO(BaseModel):
    type: str
    name: str
    description: str

class EnumTableResponseDTO(BaseModel):
    id: int
    type: str
    name: str
    description: str
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