from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from ..base_model import Base

class RoleEntity(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    groups = Column(String(255), nullable=True)  # e.g., "2,3,4"
    
    created_at = Column(DateTime)
    created_by = Column(String)
    updated_at = Column(DateTime)
    updated_by = Column(String)
    deleted_at = Column(DateTime)

    # Relationships
    user = relationship("UserEntity", back_populates="role")
    menu = relationship("MenuEntity", back_populates="role")


class RoleDTO(BaseModel):
    name: str
    groups: Optional[str] = None

class RoleResponseDTO(BaseModel):
    id: int
    name: str
    groups: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models
        json_encoders = {
            datetime: lambda v: (
                v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v.astimezone(timezone.utc)
            ).isoformat().replace("+00:00", "Z")
        }