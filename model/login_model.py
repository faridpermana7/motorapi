from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import relationship

from model.user_model import UserDTO
from .base_model import Base

# Login Entity (Database Model)
class LoginEntity(Base):
    __tablename__ = "logins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    time = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_login = Column(Boolean, nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(512))
    location = Column(String(256))
    created_at = Column(DateTime)
    created_by = Column(String)
    updated_at = Column(DateTime)
    updated_by = Column(String)
    deleted_at = Column(DateTime)

    # relationship back to user
    user = relationship("UserEntity", back_populates="logins")

    @property
    def username(self) -> str:
        return self.user.username if self.user else None


# Login DTO (API Model)
class LoginDTO(BaseModel):
    user_id: int
    time: datetime
    is_login: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    location: Optional[str] = None

class LoginResponseDTO(BaseModel):
    id: int
    user_id: int
    user: UserDTO
    time: datetime
    is_login: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    location: Optional[str] = None
    created_at: Optional[datetime]
    created_by: Optional[str]
    updated_at: Optional[datetime]
    updated_by: Optional[str]
    deleted_at: Optional[datetime]


    class Config:
        orm_mode = True
        from_attributes = True  # Allows conversion from SQLAlchemy models
        json_encoders = {
            datetime: lambda v: (
                v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v.astimezone(timezone.utc)
            ).isoformat().replace("+00:00", "Z")
        }