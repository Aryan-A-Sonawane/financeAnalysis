"""Policy query endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.schemas import PolicyCoverageRequest, PolicyCoverageResponse, TokenData
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/{policy_id}/coverage", response_model=PolicyCoverageResponse)
async def get_policy_coverage(
    policy_id: str,
    service_category: str | None = None,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get coverage details for a policy.
    
    Returns:
    - All coverages under the policy
    - Exclusions
    - Limitations
    """
    logger.info(
        "policy_coverage_requested",
        policy_id=policy_id,
        user_id=current_user.user_id,
        service_category=service_category,
    )
    
    # TODO: Implement policy query
    # 1. Query NebulaGraph for policy
    # 2. Get all coverages
    # 3. Get exclusions
    # 4. Filter by service category if provided
    
    return PolicyCoverageResponse(
        policy_id=policy_id,
        coverages=[],
        exclusions=[],
        limitations=[],
    )


@router.get("/{policy_id}/graph")
async def get_policy_graph(
    policy_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get policy graph structure.
    
    Returns the graph representation showing:
    - Policy node
    - Connected coverage nodes
    - Exclusion relationships
    - Applicable procedures/diagnoses
    """
    logger.info(
        "policy_graph_requested",
        policy_id=policy_id,
        user_id=current_user.user_id,
    )
    
    # TODO: Query NebulaGraph and return graph structure
    
    return {
        "policy_id": policy_id,
        "nodes": [],
        "edges": [],
    }
