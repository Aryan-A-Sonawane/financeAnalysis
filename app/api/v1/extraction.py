"""Entity extraction endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.schemas import EntityExtractionRequest, EntityExtractionResponse, TokenData
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/extract", response_model=EntityExtractionResponse)
async def extract_entities(
    request: EntityExtractionRequest,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Extract structured entities from a document.
    
    Extracts:
    - Policy entities (deductibles, copays, limits)
    - Claim entities (CPT codes, ICD-10, amounts)
    - Invoice entities (line items, totals)
    """
    logger.info(
        "extraction_requested",
        document_id=str(request.document_id),
        user_id=current_user.user_id,
        entity_types=request.entity_types,
    )
    
    # TODO: Implement extraction workflow
    # 1. Retrieve document from database
    # 2. Run extraction agent
    # 3. Store entities in graph and vector databases
    # 4. Return extracted entities
    
    return EntityExtractionResponse(
        document_id=request.document_id,
        entities={
            "policies": [],
            "coverages": [],
            "procedures": [],
            "diagnoses": [],
            "claims": [],
        },
        confidence_scores={},
    )
