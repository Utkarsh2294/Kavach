from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from uuid import UUID

from app.database import get_db
from app.deps import get_current_org_id
from app.models import AuditLog
from app.services.audit import GENESIS_HASH, calculate_hash
from app.schemas.audit import AuditLogResponse, AuditVerifyResponse, NistMappingResponse

router = APIRouter(prefix='/api/v1', tags=['Audit & Compliance'])


@router.get("/audit", response_model=List[AuditLogResponse])
async def get_audit_log(
    sandbox: bool = False,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.org_id == org_id, AuditLog.is_sandbox == sandbox)
        .order_by(AuditLog.timestamp.desc())
        .limit(500)
    )
    return list(result.scalars().all())

@router.get("/audit/verify", response_model=AuditVerifyResponse)
async def verify_audit_log(
    sandbox: bool = False,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AuditLog).where(
        AuditLog.org_id == org_id, AuditLog.is_sandbox == sandbox
    ).order_by(AuditLog.timestamp.asc(), AuditLog.id.asc())
    result = await db.execute(stmt)
    entries = list(result.scalars().all())
    previous_hash = GENESIS_HASH
    breaks = []
    for entry in entries:
        expected = calculate_hash(previous_hash, entry.payload)
        if entry.prev_hash != previous_hash or entry.this_hash != expected:
            breaks.append({"recordId": str(entry.id), "expectedHash": expected,
                           "actualHash": entry.this_hash})
        previous_hash = entry.this_hash or ""

    return AuditVerifyResponse(
        valid=not breaks,
        records_verified=len(entries),
        breaks=breaks,
    )

@router.get("/compliance/nist-mapping", response_model=NistMappingResponse)
async def get_nist_mapping():
    mappings = [
        {
            "category": "GOVERN",
            "description": "Policies and processes to oversee AI system life cycles",
            "subcategories": [
                "Policy Establishment (GOVERN 1.1)",
                "Accountability (GOVERN 1.2)",
                "Training & Culture (GOVERN 2)",
            ],
        },
        {
            "category": "MAP",
            "description": "Establish the context of the AI system",
            "subcategories": [
                "System Mapping (MAP 1.1)",
                "Risk Identification (MAP 2.1)",
            ],
        },
        {
            "category": "MEASURE",
            "description": "Assess & quantify risk",
            "subcategories": [
                "Bias & Accuracy (MEASURE 1.1)",
                "Performance Monitoring (MEASURE 3.1)",
            ],
        },
        {
            "category": "MANAGE",
            "description": "Treat and control risk",
            "subcategories": [
                "Incident Response (MANAGE 1.1)",
                "Explainability (MANAGE 2.1)",
            ],
        },
    ]
    return NistMappingResponse(mappings=mappings)
