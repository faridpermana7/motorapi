from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import relationship
from ..base_model import Base

# User Entity (Database Model)
class UserEntity(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    username = Column(String, nullable=False)
    email = Column(String)
    password_hash = Column(Text, nullable=False)
    created_at = Column(DateTime)
    created_by = Column(String)
    updated_at = Column(DateTime)
    updated_by = Column(String)
    deleted_at = Column(DateTime)

    # Relationships
    role = relationship("RoleEntity", back_populates="user")
    
    # Referenced by:
    logins = relationship("LoginEntity", back_populates="user")

    
    @property
    def role_name(self) -> str:
        return self.role.name if self.role else None


# User DTO (API Model)
class UserDTO(BaseModel):
    username: str
    email: str
    role_id: int
    password: Optional[str] = None  

    class Config:
        from_attributes = True

class UserResponseDTO(BaseModel):
    id: int
    username: str
    email: str 
    password_hash: str
    role_id: Optional[int] = None
    role_name: Optional[str] = None
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