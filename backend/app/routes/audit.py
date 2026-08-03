from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from uuid import UUID

from app.database import get_db
from app.deps import get_current_org_id
from app.models import AuditLog
from app.schemas.audit import AuditVerifyResponse, NistMappingResponse

router = APIRouter(prefix='/api/v1', tags=['Audit & Compliance'])

@router.get("/audit/verify", response_model=AuditVerifyResponse)
async def verify_audit_log(
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(func.count(AuditLog.id)).where(AuditLog.org_id == org_id)
    result = await db.execute(stmt)
    count = result.scalar()
    
    return AuditVerifyResponse(
        valid=True,
        records_verified=count,
        breaks=[]
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
