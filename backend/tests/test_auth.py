import uuid
import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import HTTPException

from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.deps import ROLE_HIERARCHY, require_role
from app.config import get_settings


# 1. test_hash_password_returns_bcrypt_hash
def test_hash_password_returns_bcrypt_hash():
    password = "MySuperSecretPassword123"
    hashed = hash_password(password)
    # bcrypt hashes usually start with $2b$ (or $2a$ / $2y$)
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

# 2. test_verify_password_correct
def test_verify_password_correct():
    password = "MySuperSecretPassword123"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True

# 3. test_verify_password_incorrect
def test_verify_password_incorrect():
    password = "MySuperSecretPassword123"
    wrong_password = "WrongPassword"
    hashed = hash_password(password)
    assert verify_password(wrong_password, hashed) is False

# 4. test_password_never_in_hash
def test_password_never_in_hash():
    password = "MySuperSecretPassword123"
    hashed = hash_password(password)
    assert password not in hashed

# 5. test_create_access_token_decodable
def test_create_access_token_decodable():
    user_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())
    role = "admin"
    
    token = create_access_token(user_id=user_id, org_id=org_id, role=role)
    payload = decode_token(token)
    
    assert payload["sub"] == user_id
    assert payload["org_id"] == org_id
    assert payload["role"] == role

# 6. test_access_token_type_is_access
def test_access_token_type_is_access():
    user_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())
    role = "viewer"
    
    token = create_access_token(user_id=user_id, org_id=org_id, role=role)
    payload = decode_token(token)
    
    assert payload.get("type") == "access"

# 7. test_refresh_token_type_is_refresh
def test_refresh_token_type_is_refresh():
    user_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())
    role = "reviewer"
    
    token = create_refresh_token(user_id=user_id, org_id=org_id, role=role)
    payload = decode_token(token)
    
    assert payload.get("type") == "refresh"

# 8. test_refresh_token_has_session_id
def test_refresh_token_has_session_id():
    user_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())
    role = "operator"
    
    token = create_refresh_token(user_id=user_id, org_id=org_id, role=role)
    payload = decode_token(token)
    
    assert "sid" in payload
    assert payload["sid"] is not None

# 9. test_expired_token_raises
def test_expired_token_raises():
    settings = get_settings()
    payload = {
        'sub': str(uuid.uuid4()),
        'org_id': str(uuid.uuid4()),
        'role': 'admin',
        'type': 'access',
        'exp': datetime.now(timezone.utc) - timedelta(hours=1),
    }
    
    # Support both case variations depending on how settings are defined
    secret = getattr(settings, 'secret_key', getattr(settings, 'SECRET_KEY', 'secret'))
    token = jwt.encode(payload, secret, algorithm='HS256')
    
    with pytest.raises(JWTError):
        decode_token(token)

# 10. test_invalid_token_string_raises
def test_invalid_token_string_raises():
    with pytest.raises(JWTError):
        decode_token("this.is.not_a_valid_token")

# 11. test_role_hierarchy_ordering
def test_role_hierarchy_ordering():
    assert ROLE_HIERARCHY["viewer"] < ROLE_HIERARCHY["reviewer"]
    assert ROLE_HIERARCHY["reviewer"] < ROLE_HIERARCHY["operator"]
    assert ROLE_HIERARCHY["operator"] < ROLE_HIERARCHY["admin"]

# 12. test_viewer_cannot_access_operator_endpoint
@pytest.mark.asyncio
async def test_viewer_cannot_access_operator_endpoint():
    checker = require_role("operator")
    # The inner function expects a dict with 'role' key (JWT payload shape)
    viewer_payload = {"sub": str(uuid.uuid4()), "org_id": str(uuid.uuid4()), "role": "viewer", "type": "access"}
    
    with pytest.raises(HTTPException) as exc:
        await checker(user=viewer_payload)
    
    assert exc.value.status_code == 403

# 13. test_admin_can_access_all
@pytest.mark.asyncio
async def test_admin_can_access_all():
    checker = require_role("viewer")
    admin_payload = {"sub": str(uuid.uuid4()), "org_id": str(uuid.uuid4()), "role": "admin", "type": "access"}
    
    try:
        await checker(user=admin_payload)
    except HTTPException:
        pytest.fail("Admin should be able to access viewer endpoint")

# 14. test_cross_org_isolation
def test_cross_org_isolation():
    user_id = str(uuid.uuid4())
    org1_id = str(uuid.uuid4())
    org2_id = str(uuid.uuid4())
    
    token1 = create_access_token(user_id=user_id, org_id=org1_id, role="viewer")
    token2 = create_access_token(user_id=user_id, org_id=org2_id, role="viewer")
    
    payload1 = decode_token(token1)
    payload2 = decode_token(token2)
    
    assert payload1["org_id"] == org1_id
    assert payload2["org_id"] == org2_id
    assert payload1["org_id"] != payload2["org_id"]
