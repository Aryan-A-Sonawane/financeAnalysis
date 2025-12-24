"""Simplified FastAPI app for demo with mock endpoints."""

from fastapi import FastAPI, HTTPException, File, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uvicorn
import os
import uuid

app = FastAPI(
    title="FinSightAI - Demo Mode",
    description="Financial Document Intelligence Platform (Demo Mode - Mock endpoints for testing)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create temp directory for uploads
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class HealthResponse(BaseModel):
    status: str
    message: str
    services: dict


class DocumentMetadata(BaseModel):
    id: str
    filename: str
    file_type: str
    upload_time: str
    size_bytes: int
    status: str
    message: str


class ExtractionResult(BaseModel):
    document_id: str
    entities: dict
    confidence: float
    processing_time: float


class WorkflowResult(BaseModel):
    workflow_id: str
    status: str
    results: dict
    processing_time: float


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to FinSightAI Platform - Demo Mode",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "Running with mock endpoints for demonstration",
        "note": "Upload documents to see simulated processing results"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "API is running in demo mode with mock data",
        "services": {
            "api": "✅ Running",
            "database": "🔄 Mock mode (simulated responses)",
            "storage": "🔄 Local temp storage",
            "ai_services": "🔄 Mock mode (simulated analysis)",
        },
    }


@app.get("/info", tags=["Info"])
async def api_info():
    """API information."""
    return {
        "project": "FinSightAI - Financial Document Intelligence",
        "demo_mode": "Active - All endpoints return simulated results",
        "features": [
            "✅ Document Upload (saves to temp folder)",
            "🔄 AI-powered Classification (simulated)",
            "🔄 Entity Extraction (simulated)",
            "🔄 Claims Eligibility Analysis (simulated)",
            "🔄 Fraud Detection (simulated)",
            "🔄 Workflow Processing (simulated)",
        ],
        "tech_stack": {
            "framework": "FastAPI",
            "databases": ["PostgreSQL (not connected)", "NebulaGraph (not connected)", "Weaviate (not connected)"],
            "storage": "Temporary local storage",
            "ai": "Mock responses for demonstration",
        },
        "instructions": [
            "1. Upload documents via /api/v1/documents/upload",
            "2. View simulated processing results",
            "3. Test workflow endpoints with mock data",
            "4. To enable full functionality: connect Docker services and initialize databases",
        ],
    }


# ============================================================================
# DOCUMENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/documents/upload", response_model=DocumentMetadata, status_code=status.HTTP_201_CREATED, tags=["Documents"])
async def upload_document(
    file: UploadFile = File(...),
):
    """
    Upload a document for processing (Demo Mode - saves locally).
    
    Supported formats: PDF, DOCX, JPEG, PNG, TXT
    
    Args:
        file: Document file to upload
    
    Returns:
        Document metadata with simulated processing status
    """
    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image/jpeg",
        "image/png",
        "text/plain",
    ]
    
    if file.content_type and file.content_type not in allowed_types:
        # Still allow it but warn
        pass

    # Read and save file
    content = await file.read()
    file_size = len(content)
    
    # Save to temp directory
    doc_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{file.filename}")
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    return DocumentMetadata(
        id=doc_id,
        filename=file.filename,
        file_type=file.content_type or "unknown",
        upload_time=datetime.utcnow().isoformat(),
        size_bytes=file_size,
        status="uploaded",
        message=f"✅ Document uploaded successfully! Saved to {file_path}. In production, this would trigger AI processing workflows."
    )


@app.get("/api/v1/documents/{document_id}", response_model=DocumentMetadata, tags=["Documents"])
async def get_document(document_id: str):
    """Get document metadata (Mock response)."""
    return DocumentMetadata(
        id=document_id,
        filename="sample_document.pdf",
        file_type="application/pdf",
        upload_time=datetime.utcnow().isoformat(),
        size_bytes=1024000,
        status="processed",
        message="Document metadata (mock data for demo)"
    )


@app.get("/api/v1/documents/", tags=["Documents"])
async def list_documents():
    """List all uploaded documents (Mock response)."""
    return {
        "total": 2,
        "documents": [
            {
                "id": "doc-001",
                "filename": "insurance_claim.pdf",
                "file_type": "application/pdf",
                "upload_time": "2025-12-24T10:00:00",
                "status": "processed"
            },
            {
                "id": "doc-002",
                "filename": "medical_invoice.pdf",
                "file_type": "application/pdf",
                "upload_time": "2025-12-24T11:00:00",
                "status": "processed"
            }
        ],
        "note": "Mock data for demonstration"
    }


# ============================================================================
# EXTRACTION ENDPOINTS
# ============================================================================

@app.post("/api/v1/extraction/extract", response_model=ExtractionResult, tags=["Extraction"])
async def extract_entities(
    file: UploadFile = File(...),
):
    """
    Extract entities from a document (Mock response).
    
    In production, this uses AI to extract:
    - Patient information
    - Dates and amounts
    - Medical codes (ICD-10, CPT)
    - Policy numbers
    """
    content = await file.read()
    
    return ExtractionResult(
        document_id=str(uuid.uuid4()),
        entities={
            "patient_name": "John Doe (simulated)",
            "policy_number": "POL-2024-12345 (simulated)",
            "claim_amount": "$5,000 (simulated)",
            "diagnosis_codes": "Z00.00, R53.83 (simulated)",
            "procedure_codes": "99213, 99214 (simulated)",
            "dates": "2025-12-24 (simulated)",
        },
        confidence=0.95,
        processing_time=1.2
    )


# ============================================================================
# WORKFLOW ENDPOINTS
# ============================================================================

@app.post("/api/v1/workflows/document-processing", response_model=WorkflowResult, tags=["Workflows"])
async def process_document_workflow(
    file: UploadFile = File(...),
):
    """
    Execute document processing workflow (Mock response).
    
    In production, this runs a 7-agent LangGraph workflow:
    1. Document Classification
    2. OCR Extraction
    3. Entity Recognition
    4. Policy Validation
    5. Eligibility Check
    6. Fraud Detection
    7. Compliance Validation
    """
    content = await file.read()
    
    return WorkflowResult(
        workflow_id=str(uuid.uuid4()),
        status="completed",
        results={
            "classification": {
                "type": "medical_claim",
                "confidence": 0.98
            },
            "extraction": {
                "patient": "Jane Smith (simulated)",
                "provider": "City Hospital (simulated)",
                "claim_total": "$12,500 (simulated)"
            },
            "eligibility": {
                "status": "approved",
                "coverage": 80,
                "reason": "Policy active, within coverage limits"
            },
            "fraud_score": {
                "risk_level": "low",
                "score": 0.15,
                "flags": []
            },
            "compliance": {
                "status": "compliant",
                "checks_passed": 8,
                "checks_total": 8
            }
        },
        processing_time=5.3
    )


@app.post("/api/v1/workflows/eligibility-check", response_model=WorkflowResult, tags=["Workflows"])
async def check_eligibility_workflow(
    policy_number: str,
    claim_details: dict,
):
    """
    Execute eligibility check workflow (Mock response).
    
    In production, this uses graph reasoning to:
    - Validate policy status
    - Check coverage limits
    - Verify benefits
    - Apply exclusions
    """
    return WorkflowResult(
        workflow_id=str(uuid.uuid4()),
        status="completed",
        results={
            "policy_status": "active",
            "eligible": True,
            "coverage_percentage": 80,
            "deductible_remaining": "$500",
            "out_of_pocket_max": "$2000 remaining",
            "benefits_applied": [
                "Outpatient services",
                "Diagnostic tests",
                "Prescription drugs"
            ],
            "exclusions_checked": [],
            "reasoning": "Policy is active and claim falls within covered benefits (simulated)"
        },
        processing_time=2.1
    )


# ============================================================================
# FRAUD DETECTION ENDPOINTS
# ============================================================================

@app.post("/api/v1/fraud/analyze", tags=["Fraud Detection"])
async def analyze_fraud_risk(
    file: UploadFile = File(...),
):
    """
    Analyze document for fraud indicators (Mock response).
    
    In production, AI analyzes:
    - Duplicate claims
    - Unusual billing patterns
    - Provider history
    - Temporal anomalies
    """
    content = await file.read()
    
    return {
        "document_id": str(uuid.uuid4()),
        "fraud_score": 0.23,
        "risk_level": "low",
        "indicators": [
            {
                "type": "billing_pattern",
                "severity": "low",
                "description": "Normal billing pattern detected"
            }
        ],
        "recommendations": [
            "No immediate action required",
            "Continue standard processing"
        ],
        "confidence": 0.92,
        "note": "Simulated fraud analysis for demonstration"
    }


# ============================================================================
# SEARCH ENDPOINTS
# ============================================================================

@app.get("/api/v1/search/similar", tags=["Search"])
async def search_similar_documents(query: str):
    """
    Search for similar documents using semantic search (Mock response).
    
    In production, uses Weaviate vector database.
    """
    return {
        "query": query,
        "results": [
            {
                "id": "doc-101",
                "filename": "similar_claim_1.pdf",
                "similarity_score": 0.94,
                "snippet": "Medical claim for outpatient procedure... (simulated)"
            },
            {
                "id": "doc-102",
                "filename": "similar_claim_2.pdf",
                "similarity_score": 0.89,
                "snippet": "Insurance claim with similar diagnosis codes... (simulated)"
            }
        ],
        "total_found": 2,
        "note": "Mock search results for demonstration"
    }


@app.get("/api/v1/search/graph", tags=["Search"])
async def search_graph(entity_type: str, entity_id: str):
    """
    Query knowledge graph (Mock response).
    
    In production, uses NebulaGraph for entity relationships.
    """
    return {
        "entity": {
            "type": entity_type,
            "id": entity_id,
        },
        "relationships": [
            {
                "type": "has_policy",
                "target": {
                    "type": "Policy",
                    "id": "POL-12345",
                    "status": "active"
                }
            },
            {
                "type": "submitted_claim",
                "target": {
                    "type": "Claim",
                    "id": "CLM-67890",
                    "amount": "$5000"
                }
            }
        ],
        "note": "Mock graph data for demonstration"
    }


# ============================================================================
# POLICY & ELIGIBILITY ENDPOINTS
# ============================================================================

@app.post("/api/v1/policy/query", tags=["Policy"])
async def query_policy(policy_number: str, question: str):
    """
    Query policy using natural language (Mock response).
    
    In production, uses AI to answer policy questions.
    """
    return {
        "policy_number": policy_number,
        "question": question,
        "answer": "Based on your policy, outpatient procedures are covered at 80% after deductible. (simulated answer)",
        "confidence": 0.91,
        "sources": [
            "Policy document section 3.2",
            "Benefits schedule page 12"
        ],
        "note": "Simulated policy analysis for demonstration"
    }


@app.get("/api/v1/eligibility/check", tags=["Eligibility"])
async def check_eligibility(policy_number: str, service_code: str):
    """Check if a service is covered (Mock response)."""
    return {
        "policy_number": policy_number,
        "service_code": service_code,
        "eligible": True,
        "coverage_percentage": 80,
        "requirements": [
            "Valid policy",
            "Within coverage limits",
            "No exclusions apply"
        ],
        "note": "Simulated eligibility check for demonstration"
    }


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  FinSightAI Platform - Demo Mode")
    print("=" * 70)
    print("\n⚠️  Running in demo mode - database services are not available")
    print("\n📋 To enable full functionality:")
    print("   1. Install Docker Desktop")
    print("   2. Run: docker compose up -d")
    print("\n🌐 API Documentation: http://localhost:8000/docs")
    print("=" * 70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
