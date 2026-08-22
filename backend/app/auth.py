import uuid
from datetime import datetime, timedelta, timezone
import bcrypt as _bcrypt
from jose import jwt, JWTError
from app.config import get_settings

ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt(rounds=12)).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def create_access_token(user_id: str, org_id: str, role: str, session_id: str | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "org_id": str(org_id),
        "role": role,
        "exp": expire,
        "type": "access",
    }
    # Carry the refresh-session id only to support server-side logout revocation;
    # it is an opaque UUID, never a credential itself.
    if session_id:
        payload["sid"] = session_id
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)

def create_refresh_token(user_id: str, org_id: str, role: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    session_id = str(uuid.uuid4())
    payload = {
        "sub": str(user_id),
        "org_id": str(org_id),
        "role": role,
        "exp": expire,
        "type": "refresh",
        "sid": session_id,  # session ID for revocation
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
