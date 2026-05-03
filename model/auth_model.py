from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from model.admin.menu_model import MenuTreeDTO

# Authentication models
class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    menus: List[MenuTreeDTO] = []  # Include menu tree in the token response  

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