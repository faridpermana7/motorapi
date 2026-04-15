from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Authentication models
class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    exp: Optional[datetime] = None

class UserInDB(BaseModel):
    id: int
    username: str
    email: str
    password_hash: str
    disabled: bool = False

    class Config:
        from_attributes = True