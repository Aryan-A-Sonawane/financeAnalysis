"""Search endpoints - Semantic search and graph queries."""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from app.services.vector_store_service import get_vector_store_service
from app.services.graph_store_service import get_graph_store_service
from app.core.security import get_current_user
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


# Request/Response Models
class SemanticSearchRequest(BaseModel):
    """Request for semantic search."""
    query: str = Field(..., description="Search query text")
    document_type: Optional[str] = Field(None, description="Filter by document type")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results")
    min_certainty: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity")


class HybridSearchRequest(BaseModel):
    """Request for hybrid search."""
    query: str = Field(..., description="Search query text")
    alpha: float = Field(default=0.7, ge=0.0, le=1.0, description="Vector weight (1.0=pure vector)")
    document_type: Optional[str] = Field(None, description="Filter by document type")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results")


class GraphQueryRequest(BaseModel):
    """Request for graph query."""
    entity_id: str = Field(..., description="Entity vertex ID")
    relationship_type: Optional[str] = Field(None, description="Filter by relationship type")
    direction: str = Field(default="both", description="Relationship direction: in, out, both")


class CoveragePathRequest(BaseModel):
    """Request for coverage path query."""
    policy_id: str = Field(..., description="Policy identifier")
    service_code: str = Field(..., description="Service/procedure code")
    max_hops: int = Field(default=3, ge=1, le=5, description="Maximum graph hops")


class SimilarClaimsRequest(BaseModel):
    """Request for similar claims query."""
    diagnosis_codes: List[str] = Field(..., description="ICD-10 diagnosis codes")
    procedure_codes: List[str] = Field(..., description="CPT procedure codes")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results")


@router.post("/semantic", response_model=Dict[str, Any])
async def semantic_search(
    request: SemanticSearchRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Perform semantic search across documents.
    
    Uses vector embeddings to find documents similar to the query.
    Returns documents ranked by semantic similarity.
    """
    try:
        vector_store = get_vector_store_service()
        
        results = await vector_store.semantic_search(
            query=request.query,
            document_type=request.document_type,
            user_id=current_user.get("user_id"),
            limit=request.limit,
            min_certainty=request.min_certainty
        )
        
        logger.info(
            "Semantic search completed",
            query=request.query[:100],
            result_count=len(results),
            user_id=current_user.get("user_id")
        )
        
        return {
            "success": True,
            "query": request.query,
            "result_count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(
            "Semantic search failed",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/hybrid", response_model=Dict[str, Any])
async def hybrid_search(
    request: HybridSearchRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Perform hybrid search (vector + keyword).
    
    Combines semantic vector search with traditional keyword matching.
    Alpha parameter controls the blend (1.0 = pure vector, 0.0 = pure keyword).
    """
    try:
        vector_store = get_vector_store_service()
        
        results = await vector_store.hybrid_search(
            query=request.query,
            alpha=request.alpha,
            document_type=request.document_type,
            limit=request.limit
        )
        
        logger.info(
            "Hybrid search completed",
            query=request.query[:100],
            alpha=request.alpha,
            result_count=len(results),
            user_id=current_user.get("user_id")
        )
        
        return {
            "success": True,
            "query": request.query,
            "alpha": request.alpha,
            "result_count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(
            "Hybrid search failed",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/similar/{document_id}", response_model=Dict[str, Any])
async def find_similar_documents(
    document_id: str,
    limit: int = Query(default=5, ge=1, le=20),
    min_certainty: float = Query(default=0.7, ge=0.0, le=1.0),
    current_user: Dict = Depends(get_current_user)
):
    """
    Find documents similar to a given document.
    
    Uses vector similarity to find related documents.
    """
    try:
        vector_store = get_vector_store_service()
        
        results = await vector_store.find_similar_documents(
            document_id=document_id,
            limit=limit,
            min_certainty=min_certainty
        )
        
        logger.info(
            "Similar documents found",
            document_id=document_id,
            result_count=len(results),
            user_id=current_user.get("user_id")
        )
        
        return {
            "success": True,
            "document_id": document_id,
            "result_count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(
            "Similar documents search failed",
            document_id=document_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/graph/relationships", response_model=Dict[str, Any])
async def get_entity_relationships(
    request: GraphQueryRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get relationships for an entity from knowledge graph.
    
    Returns all related entities and their relationship types.
    """
    try:
        graph_store = get_graph_store_service()
        
        results = await graph_store.get_entity_relationships(
            entity_id=request.entity_id,
            relationship_type=request.relationship_type,
            direction=request.direction
        )
        
        logger.info(
            "Entity relationships retrieved",
            entity_id=request.entity_id,
            relationship_count=len(results),
            user_id=current_user.get("user_id")
        )
        
        return {
            "success": True,
            "entity_id": request.entity_id,
            "relationship_count": len(results),
            "relationships": results
        }
        
    except Exception as e:
        logger.error(
            "Entity relationships query failed",
            entity_id=request.entity_id,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )


@router.post("/graph/coverage-path", response_model=Dict[str, Any])
async def query_coverage_path(
    request: CoveragePathRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Query coverage path from policy to service.
    
    Finds graph paths showing how a policy covers a specific service.
    Useful for eligibility determination and coverage verification.
    """
    try:
        graph_store = get_graph_store_service()
        
        paths = await graph_store.query_coverage_path(
            policy_id=request.policy_id,
            service_code=request.service_code,
            max_hops=request.max_hops
        )
        
        logger.info(
            "Coverage path query completed",
            policy_id=request.policy_id,
            service_code=request.service_code,
            paths_found=len(paths),
            user_id=current_user.get("user_id")
        )
        
        return {
            "success": True,
            "policy_id": request.policy_id,
            "service_code": request.service_code,
            "paths_found": len(paths),
            "covered": len(paths) > 0,
            "paths": paths
        }
        
    except Exception as e:
        logger.error(
            "Coverage path query failed",
            policy_id=request.policy_id,
            service_code=request.service_code,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )


@router.post("/graph/similar-claims", response_model=Dict[str, Any])
async def find_similar_claims(
    request: SimilarClaimsRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Find similar historical claims.
    
    Uses knowledge graph to find claims with similar diagnoses and procedures.
    Useful for cost estimation and fraud detection.
    """
    try:
        graph_store = get_graph_store_service()
        
        claims = await graph_store.find_similar_claims(
            diagnosis_codes=request.diagnosis_codes,
            procedure_codes=request.procedure_codes,
            limit=request.limit
        )
        
        logger.info(
            "Similar claims found",
            diagnosis_count=len(request.diagnosis_codes),
            procedure_count=len(request.procedure_codes),
            claims_found=len(claims),
            user_id=current_user.get("user_id")
        )
        
        return {
            "success": True,
            "diagnosis_codes": request.diagnosis_codes,
            "procedure_codes": request.procedure_codes,
            "claims_found": len(claims),
            "claims": claims
        }
        
    except Exception as e:
        logger.error(
            "Similar claims query failed",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_search_stats(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get search and vector store statistics.
    
    Returns stats about indexed documents and graph entities.
    """
    try:
        vector_store = get_vector_store_service()
        
        stats = await vector_store.get_document_stats(
            user_id=current_user.get("user_id")
        )
        
        logger.info(
            "Search stats retrieved",
            user_id=current_user.get("user_id")
        )
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(
            "Stats retrieval failed",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Stats retrieval failed: {str(e)}"
        )
