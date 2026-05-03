from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import relationship 
from ..base_model import Base

# Menu Entity (Database Model)
class MenuEntity(Base):
    __tablename__ = "menus"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    parent_id = Column(Integer, ForeignKey("menus.id"), nullable=True)
    label = Column(String(100), nullable=False)
    path = Column(String(200), nullable=True)   # allow NULL for parent menus
    icon = Column(String(50)) 
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime)
    created_by = Column(String)
    updated_at = Column(DateTime)
    updated_by = Column(String)
    deleted_at = Column(DateTime) 

    # Self-referential relationship
    parent = relationship("MenuEntity", remote_side=[id], back_populates="children")

    children = relationship(
        "MenuEntity",
        back_populates="parent",
        cascade="all, delete-orphan"
    )

    @property
    def parent_name(self) -> str:
        return self.parent.label if self.parent else None

# Menu DTO (API Model)
class MenuDTO(BaseModel):
    parent_id: Optional[int]
    label: str
    path: Optional[str]  
    icon: Optional[str]
    is_active: bool = False
    sort_order: int = 0

class MenuResponseDTO(BaseModel):
    id: int
    parent_id: Optional[int]
    parent_name: Optional[str] = None
    label: str
    path: Optional[str]
    icon: Optional[str]
    is_active: bool
    sort_order: int
    created_at: Optional[datetime]
    created_by: Optional[str]
    updated_at: Optional[datetime]
    updated_by: Optional[str]
    deleted_at: Optional[datetime]

    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models to Pydantic models
        orm_mode = True
        json_encoders = {
            datetime: lambda v: (
                v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v.astimezone(timezone.utc)
            ).isoformat().replace("+00:00", "Z")
        }

class MenuTreeDTO(BaseModel):
    id: int
    label: str
    path: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool
    sort_order: int
    children: List["MenuTreeDTO"] = []  # recursive children

    created_at: Optional[datetime]
    created_by: Optional[str]
    updated_at: Optional[datetime]
    updated_by: Optional[str]
    deleted_at: Optional[datetime]

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: (
                v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v.astimezone(timezone.utc)
            ).isoformat().replace("+00:00", "Z")
        }