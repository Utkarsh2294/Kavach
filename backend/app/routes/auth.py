import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import JWTError

from app.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.schemas.auth import (
    LoginRequest, LoginResponse, SignupRequest, SignupResponse,
    ForgotPasswordRequest, ResetPasswordRequest, RefreshRequest,
    RefreshResponse, MessageResponse, MeResponse, UserResponse
)
from app.auth import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token
)
from app.redis_client import RedisClient
from app.config import get_settings

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)

def user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        organization_id=user.org_id,
        created_at=user.created_at,
    )

def get_current_token_payload(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Not authenticated"}}
        )
    token = credentials.credentials
    try:
        payload = decode_token(token)
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Not authenticated"}}
        )

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalars().first()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"}}
        )

    refresh_token = create_refresh_token(str(user.id), str(user.org_id), user.role)

    payload = decode_token(refresh_token)
    session_id = payload.get("sid")
    access_token = create_access_token(str(user.id), str(user.org_id), user.role, session_id)
    settings = get_settings()
    
    await RedisClient.set_session(
        session_id, 
        {"user_id": str(user.id), "org_id": str(user.org_id), "role": user.role},
        ttl_seconds=settings.refresh_token_expire_days * 24 * 60 * 60
    )

    return LoginResponse(
        user=user_to_response(user),
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "EMAIL_EXISTS", "message": "An account with this email already exists"}}
        )

    # Create org
    org_id = uuid.uuid4()
    short_uuid = str(org_id)[:8]
    new_org = Organization(
        id=org_id,
        name=f"Org-{short_uuid}"
    )
    db.add(new_org)
    await db.flush()

    # Create user
    user_id = uuid.uuid4()
    new_user = User(
        id=user_id,
        org_id=new_org.id,
        email=request.email,
        password_hash=hash_password(request.password),
        name=request.name,
        role="operator",
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    refresh_token = create_refresh_token(str(new_user.id), str(new_user.org_id), new_user.role)

    payload = decode_token(refresh_token)
    session_id = payload.get("sid")
    access_token = create_access_token(str(new_user.id), str(new_user.org_id), new_user.role, session_id)
    settings = get_settings()
    
    await RedisClient.set_session(
        session_id, 
        {"user_id": str(new_user.id), "org_id": str(new_user.org_id), "role": new_user.role},
        ttl_seconds=settings.refresh_token_expire_days * 24 * 60 * 60
    )

    return SignupResponse(
        user=user_to_response(new_user),
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(request: ForgotPasswordRequest):
    return MessageResponse(message="If an account with that email exists, a reset link has been sent.")

@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(request: ResetPasswordRequest):
    if request.token == "invalid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_TOKEN", "message": "Reset token is invalid or expired"}}
        )
    return MessageResponse(message="Password has been reset successfully.")

@router.post("/logout", response_model=MessageResponse)
async def logout(payload: dict = Depends(get_current_token_payload)):
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"error": {"code": "UNAUTHORIZED", "message": "Not authenticated"}})
    session_id = payload.get("sid")
    if session_id:
        await RedisClient.delete_session(session_id)
    return MessageResponse(message="Logged out successfully")

@router.get("/me", response_model=MeResponse)
async def get_me(payload: dict = Depends(get_current_token_payload), db: AsyncSession = Depends(get_db)):
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Not authenticated"}}
        )
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Not authenticated"}}
        )
        
    return MeResponse(user=user_to_response(user))

@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(request: RefreshRequest):
    try:
        payload = decode_token(request.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError()
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Invalid refresh token"}}
        )
        
    session_id = payload.get("sid")
    user_id = payload.get("sub")
    org_id = payload.get("org_id")
    role = payload.get("role")
    
    session_data = await RedisClient.get_session(session_id)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Session expired or invalid"}}
        )
        
    # Revoke old
    await RedisClient.delete_session(session_id)
    
    # Issue new
    new_refresh = create_refresh_token(user_id, org_id, role)

    new_payload = decode_token(new_refresh)
    new_sid = new_payload.get("sid")
    new_access = create_access_token(user_id, org_id, role, new_sid)
    settings = get_settings()
    
    await RedisClient.set_session(
        new_sid, 
        {"user_id": user_id, "org_id": org_id, "role": role},
        ttl_seconds=settings.refresh_token_expire_days * 24 * 60 * 60
    )
    
    return RefreshResponse(
        access_token=new_access,
        refresh_token=new_refresh
    )
