from datetime import datetime, timedelta
import os
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from database_sqlalchemy import get_db
from model.auth_model import UserLogin, Token, TokenData, UserInDB
from model.login_model import LoginDTO
from model.user_model import UserEntity
from services.login_service import LoginRepository

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")
ALGORITHM = os.getenv("ALGORITHM")
if not ALGORITHM:
    raise ValueError("ALGORITHM environment variable is required")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES") or 30)  # Token expires in 30 minutes

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    async def get_user(self, username: str) -> Optional[UserInDB]:
        """Get user by username."""
        result = await self.session.execute(
            select(UserEntity).where(UserEntity.username == username)
        )
        user = result.scalars().first()
        if user:
            return UserInDB.from_orm(user)
        return None

    async def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with username and password."""
        user = await self.get_user(username)
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    async def get_current_user(self, token: str) -> Optional[UserInDB]:
        """Get current user from JWT token."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username, user_id=user_id)
        except JWTError:
            raise credentials_exception

        user = await self.get_user(username=token_data.username)
        if user is None:
            raise credentials_exception
        return user

    async def login(
        self,
        user_credentials: UserLogin,
        ip_address: Optional[str] = None,
        location: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Optional[Token]:
        """Login user and return access token."""
        user = await self.authenticate_user(user_credentials.username, user_credentials.password)
        if not user:
            return None
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            data={"sub": user.username, "user_id": user.id}, expires_delta=access_token_expires
        )

        # Automatically create a login record on successful authentication.
        login_data = LoginDTO(
            user_id=user.id,
            time=datetime.utcnow(),
            is_login=True,
            ip_address=ip_address,
            location=location,
            user_agent=user_agent,
        )
        login_repo = LoginRepository(self.session)
        await login_repo.create_login(login_data, user=user.username)

        return Token(access_token=access_token, token_type="bearer")

    async def logout(self, user: UserInDB) -> bool:
        login_repo = LoginRepository(self.session)
        last_login = await login_repo.get_last_login_by_id(user.id)
        if not last_login:
            raise HTTPException(status_code=400, detail="No active session found")
        
        
        """Record a logout event for the current user."""
        login_data = LoginDTO(
            user_id=user.id,
            time=datetime.utcnow(),
            is_login=False,
            ip_address=last_login.ip_address,
            location=last_login.location,
            user_agent=last_login.user_agent,
        )


        await login_repo.create_login(login_data, user=user.username)
        return True

# Dependency function for FastAPI
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> UserInDB:
    """Dependency to get current authenticated user."""
    auth_service = AuthService(db)
    return await auth_service.get_current_user(token)