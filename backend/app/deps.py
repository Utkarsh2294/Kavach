import uuid
from fastapi import Depends

# These are the seed data UUIDs from app/seed.py
# They use uuid5 with namespace 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
_NS = uuid.UUID('a1b2c3d4-e5f6-7890-abcd-ef1234567890')
DEFAULT_ORG_ID = uuid.uuid5(_NS, 'meridian-financial')
DEFAULT_USER_ID = uuid.uuid5(_NS, 'admin-user')

async def get_current_org_id() -> uuid.UUID:
    """Stub: returns the seeded org ID. Phase 07 replaces with JWT extraction."""
    return DEFAULT_ORG_ID

async def get_current_user_id() -> uuid.UUID:
    """Stub: returns the seeded admin user ID. Phase 07 replaces with JWT extraction."""
    return DEFAULT_USER_ID
