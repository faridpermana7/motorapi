from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime, timezone

from .base_model import Base

# Phrase Entity (Database Model)
class PhraseEntity(Base):
    __tablename__ = "phrases"
    id = Column(Integer, primary_key=True, index=True)
    phrase = Column(String, nullable=False)
    translation = Column(String, nullable=False)
    updated_by = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)

# Phrase DTO (API Model)
class PhraseDTO(BaseModel):
    phrase: str
    translation: str
    updated_by: str

class PhraseResponseDTO(BaseModel):
    id: int
    phrase: str
    translation: str
    updated_at: datetime
    updated_by: str

    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models