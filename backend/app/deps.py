import uuid
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import get_settings

ALGORITHM = "HS256"

# Scheme — extracts Bearer token from Authorization header
security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Decode and validate the JWT access token.
    Returns the full payload: {sub, org_id, role, exp, type}.
    Raises 401 if token is missing, invalid, or expired.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Not authenticated"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    settings = get_settings()
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid or expired token"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid token type"},
        )
    
    return payload

async def get_current_org_id(user: dict = Depends(get_current_user)) -> uuid.UUID:
    """Extract org_id from the validated JWT payload."""
    return uuid.UUID(user["org_id"])

async def get_current_user_id(user: dict = Depends(get_current_user)) -> uuid.UUID:
    """Extract user_id (sub) from the validated JWT payload."""
    return uuid.UUID(user["sub"])

# ── RBAC ─────────────────────────────────────────────────────────────────────

ROLE_HIERARCHY = {
    "viewer": 0,
    "reviewer": 1,
    "operator": 2,
    "admin": 3,
}

def require_role(min_role: str):
    """
    FastAPI dependency factory that enforces a minimum role level.
    
    Usage:
        @router.post("/kill", dependencies=[Depends(require_role("admin"))])
    
    Role hierarchy (least to most privilege):
        viewer < reviewer < operator < admin
    """
    min_level = ROLE_HIERARCHY.get(min_role, 0)
    
    async def _check_role(user: dict = Depends(get_current_user)):
        user_role = user.get("role", "viewer")
        user_level = ROLE_HIERARCHY.get(user_role, 0)
        if user_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": f"{min_role} role required"},
            )
        return user
    
    return _check_role
