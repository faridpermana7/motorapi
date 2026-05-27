from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional

from ..base_model import Base

# Configuration Entity (Database Model)
class ConfigurationEntity(Base):
    __tablename__ = "configurations"
    id = Column(Integer, primary_key=True, index=True)
    module = Column(String, nullable=False)
    type = Column(String, nullable=False)
    attribute = Column(String, nullable=False)
    value = Column(String, nullable=False)
    created_at = Column(DateTime)
    created_by = Column(String)
    updated_at = Column(DateTime)
    updated_by = Column(String)
    deleted_at = Column(DateTime)
    

# Configuration DTO (API Model)
class ConfigurationDTO(BaseModel):
    id:int
    module: str
    type: str
    attribute: str
    value: str

class ConfigurationResponseDTO(BaseModel):
    id: int
    module: str
    type: str
    attribute: str
    value: str
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