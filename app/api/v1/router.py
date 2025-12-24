"""Main API router."""

from fastapi import APIRouter

from app.api.v1 import auth, documents, eligibility, extraction, fraud, policy, workflows, search

api_router = APIRouter()

# Include sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(extraction.router, prefix="/extraction", tags=["Extraction"])
api_router.include_router(eligibility.router, prefix="/eligibility", tags=["Eligibility"])
api_router.include_router(policy.router, prefix="/policy", tags=["Policy"])
api_router.include_router(fraud.router, prefix="/fraud", tags=["Fraud Detection"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])


@api_router.get("/")
async def api_root():
    """API root endpoint."""
    return {
        "message": "FinSightAI API v1",
        "endpoints": [
            "/auth - Authentication",
            "/documents - Document management",
            "/extraction - Entity extraction",
            "/eligibility - Claims eligibility",
            "/policy - Policy queries",
            "/fraud - Fraud detection",
            "/workflows - LangGraph AI workflows",
            "/search - Semantic search & graph queries",
        ],
    }
