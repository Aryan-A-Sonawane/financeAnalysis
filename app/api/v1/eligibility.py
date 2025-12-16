"""Claims eligibility endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.postgres import get_db
from app.models.database import EligibilityCheck as DBEligibilityCheck
from app.models.schemas import (
    EligibilityCheckRequest,
    EligibilityCheckResponse,
    EligibilityResult,
    TokenData,
)
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/check", response_model=EligibilityCheckResponse, status_code=status.HTTP_200_OK)
async def check_eligibility(
    request: EligibilityCheckRequest,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check claims eligibility for a given scenario.
    
    This endpoint simulates claim approval by:
    1. Retrieving policy from graph database
    2. Checking coverage for procedure/diagnosis
    3. Verifying no exclusions apply
    4. Finding similar historical claims
    5. Calculating cost estimates
    6. Generating eligibility decision with explanation
    """
    logger.info(
        "eligibility_check_requested",
        user_id=current_user.user_id,
        policy_id=request.policy_id,
        procedure_code=request.procedure_code,
        diagnosis_code=request.diagnosis_code,
    )
    
    # TODO: Implement eligibility workflow
    # 1. Run LangGraph eligibility workflow
    # 2. Query NebulaGraph for policy coverage
    # 3. Check exclusions
    # 4. Query Weaviate for similar claims
    # 5. Calculate costs
    # 6. Generate explanation
    
    # Placeholder response
    from uuid import uuid4
    
    # Store eligibility check
    db_check = DBEligibilityCheck(
        user_id=current_user.user_id,
        policy_id=request.policy_id,
        procedure_code=request.procedure_code,
        diagnosis_code=request.diagnosis_code,
        result=EligibilityResult.APPROVED.value,
        confidence_score=8500,  # Store as int for precision (0.85)
        explanation={
            "decision": "approved",
            "reasoning": "Procedure is covered under policy",
        },
    )
    
    db.add(db_check)
    await db.commit()
    await db.refresh(db_check)
    
    return EligibilityCheckResponse(
        check_id=db_check.check_id,
        result=EligibilityResult.APPROVED,
        confidence_score=0.85,
        explanation="Based on policy coverage analysis, this procedure is covered.",
        cost_estimate=None,
        requirements=[],
        similar_claims=[],
        graph_path=None,
    )


@router.get("/history", response_model=list[EligibilityCheckResponse])
async def get_eligibility_history(
    limit: int = 20,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's eligibility check history."""
    from sqlalchemy import select, desc
    
    result = await db.execute(
        select(DBEligibilityCheck)
        .where(DBEligibilityCheck.user_id == current_user.user_id)
        .order_by(desc(DBEligibilityCheck.created_at))
        .limit(limit)
    )
    
    checks = result.scalars().all()
    
    # Convert to response format
    response_list = []
    for check in checks:
        response_list.append(
            EligibilityCheckResponse(
                check_id=check.check_id,
                result=check.result,
                confidence_score=check.confidence_score / 10000,
                explanation=check.explanation.get("reasoning", ""),
                cost_estimate=None,
                requirements=[],
                similar_claims=[],
                graph_path=None,
            )
        )
    
    return response_list
