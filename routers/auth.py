from datetime import timedelta
import json
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from user_agents import parse as parse_ua
from core.database_sqlalchemy import get_db
from model.auth_model import Token, UserInDB, UserLogin
from services.auth_service import AuthService

router = APIRouter()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Dependency to get AuthService
def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)

# Dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme), auth_service: AuthService = Depends(get_auth_service)) -> UserInDB:
    return await auth_service.get_current_user(token)

async def resolve_ip_location(ip: str) -> str | None:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://ipapi.co/{ip}/json/")
            if resp.status_code == 200:
                data = resp.json()
                return f"{data.get('city')}, {data.get('country_name')}"
    except Exception:
        return None
    
def get_client_ip(request: Request) -> str:
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else None


def get_user_agent(request: Request) -> str | None:
    ua_string = request.headers.get("User-Agent")
    if not ua_string:
        return None

    ua = parse_ua(ua_string)
    browser = f"{ua.browser.family} {ua.browser.version_string}".strip()
    os_info = f"{ua.os.family} {ua.os.version_string}".strip()
    device = ua.device.family or "Other"
    return json.dumps({
        "browser": browser,
        "os": os_info,
        "device": device,
    })


@router.post("/login", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login endpoint that accepts username and password and returns JWT token."""
    user_credentials = UserLogin(username=form_data.username, password=form_data.password)
    
    ip_address = get_client_ip(request)
    if ip_address and "," in ip_address:
        ip_address = ip_address.split(",")[0].strip()
        
    # Prefer client-provided location, else fallback to IP lookup
    location = request.headers.get("X-Location") or request.headers.get("X-Client-Location")
    if not location and ip_address:
        location = await resolve_ip_location(ip_address)

    user_agent = get_user_agent(request)
    token = await auth_service.login(
        user_credentials,
        ip_address=ip_address,
        location=location,
        user_agent=user_agent,
    )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

@router.get("/me", response_model=UserInDB)
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    """Get current user information (protected endpoint)."""
    return current_user

@router.post("/logout")
async def logout(
    current_user: UserInDB = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout endpoint that records a logout event."""
    await auth_service.logout(current_user)
    return {"message": "Logged out successfully"}

@router.post("/register")
async def register_user(
    user_data: dict,  # You might want to create a proper registration model
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user (optional endpoint)."""
    # This is a basic implementation - you should add proper validation
    # and check if user already exists
    hashed_password = auth_service.get_password_hash(user_data["password"])
    # Create user in database
    # This would require extending the UserEntity and service
    return {"message": "User registered successfully"}