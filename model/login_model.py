from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import relationship
from .base_model import Base

# Login Entity (Database Model)
class LoginEntity(Base):
    __tablename__ = "logins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    time = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_login = Column(Boolean, nullable=False)
    ip_address = Column(String(45))
    mac_address = Column(String(50))
    location = Column(String(100))

    # relationship back to user
    user = relationship("UserEntity", back_populates="logins")


# Login DTO (API Model)
class LoginDTO(BaseModel):
    user_id: int
    is_login: bool
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    location: Optional[str] = None

class LoginResponseDTO(BaseModel):
    id: int
    user_id: int
    time: datetime
    is_login: bool
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    location: Optional[str] = None

    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models