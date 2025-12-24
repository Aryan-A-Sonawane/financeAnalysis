"""Workflow endpoints - LangGraph agent orchestration."""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from app.workflows import DocumentProcessingWorkflow, EligibilityCheckWorkflow
from app.core.security import get_current_user
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/workflows", tags=["workflows"])

# Request/Response Models
class ProcessDocumentRequest(BaseModel):
    """Request to process a document through workflow."""
    document_id: str = Field(..., description="ID of uploaded document")
    document_text: str = Field(..., description="Extracted text from document")
    run_fraud_detection: bool = Field(default=True, description="Run fraud detection")
    run_compliance_check: bool = Field(default=True, description="Run compliance validation")


class EligibilityCheckRequest(BaseModel):
    """Request for eligibility check workflow."""
    policy_info: Dict[str, Any] = Field(..., description="Policy information")
    service_info: Dict[str, Any] = Field(..., description="Service/procedure information")
    patient_info: Dict[str, Any] = Field(..., description="Patient demographics")


class WorkflowStatus(BaseModel):
    """Workflow execution status."""
    workflow_id: str
    status: str  # "pending", "running", "completed", "failed"
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# In-memory workflow tracking (replace with DB in production)
workflow_executions: Dict[str, WorkflowStatus] = {}


@router.post("/process-document", response_model=Dict[str, Any])
async def process_document(
    request: ProcessDocumentRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """
    Process a document through the complete LangGraph workflow.
    
    This endpoint orchestrates all 7 AI agents:
    1. Document Classifier - Identifies document type
    2. Specialized Extraction - Routes to invoice/policy/claim agent
    3. Fraud Detection - Analyzes for fraud patterns
    4. Compliance Validation - Checks regulatory compliance
    
    Returns comprehensive analysis results.
    """
    try:
        workflow_id = str(uuid.uuid4())
        
        logger.info(
            "Starting document processing workflow",
            workflow_id=workflow_id,
            document_id=request.document_id,
            user_id=current_user.get("user_id")
        )
        
        # Track workflow execution
        workflow_executions[workflow_id] = WorkflowStatus(
            workflow_id=workflow_id,
            status="running",
            started_at=datetime.utcnow()
        )
        
        # Initialize workflow
        workflow = DocumentProcessingWorkflow()
        
        # Process document
        result = await workflow.process_document(
            document_id=request.document_id,
            document_text=request.document_text
        )
        
        # Update workflow status
        workflow_executions[workflow_id].status = "completed"
        workflow_executions[workflow_id].completed_at = datetime.utcnow()
        workflow_executions[workflow_id].result = result
        
        logger.info(
            "Document processing workflow completed",
            workflow_id=workflow_id,
            document_type=result.get("classification", {}).get("document_type"),
            success=result.get("success")
        )
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "document_id": request.document_id,
            "processing_time": (
                workflow_executions[workflow_id].completed_at - 
                workflow_executions[workflow_id].started_at
            ).total_seconds(),
            "result": result
        }
        
    except Exception as e:
        logger.error(
            "Document processing workflow failed",
            workflow_id=workflow_id,
            error=str(e),
            exc_info=True
        )
        
        # Update workflow status
        if workflow_id in workflow_executions:
            workflow_executions[workflow_id].status = "failed"
            workflow_executions[workflow_id].completed_at = datetime.utcnow()
            workflow_executions[workflow_id].error = str(e)
        
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}"
        )


@router.post("/check-eligibility", response_model=Dict[str, Any])
async def check_eligibility(
    request: EligibilityCheckRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Check insurance eligibility through LangGraph workflow.
    
    This endpoint runs:
    1. Eligibility Reasoning - Determines coverage eligibility
    2. Fraud Detection - Checks for fraud patterns
    3. Compliance Validation - Validates regulatory compliance
    
    Returns eligibility decision with fraud risk and compliance status.
    """
    try:
        workflow_id = str(uuid.uuid4())
        
        logger.info(
            "Starting eligibility check workflow",
            workflow_id=workflow_id,
            user_id=current_user.get("user_id")
        )
        
        # Track workflow execution
        workflow_executions[workflow_id] = WorkflowStatus(
            workflow_id=workflow_id,
            status="running",
            started_at=datetime.utcnow()
        )
        
        # Initialize workflow
        workflow = EligibilityCheckWorkflow()
        
        # Check eligibility
        result = await workflow.check_eligibility(
            policy_info=request.policy_info,
            service_info=request.service_info,
            patient_info=request.patient_info
        )
        
        # Update workflow status
        workflow_executions[workflow_id].status = "completed"
        workflow_executions[workflow_id].completed_at = datetime.utcnow()
        workflow_executions[workflow_id].result = result
        
        logger.info(
            "Eligibility check workflow completed",
            workflow_id=workflow_id,
            is_eligible=result.get("eligibility", {}).get("is_eligible"),
            fraud_risk=result.get("fraud_analysis", {}).get("risk_level")
        )
        
        return {
            "success": True,
            "workflow_id": workflow_id,
            "processing_time": (
                workflow_executions[workflow_id].completed_at - 
                workflow_executions[workflow_id].started_at
            ).total_seconds(),
            "result": result
        }
        
    except Exception as e:
        logger.error(
            "Eligibility check workflow failed",
            workflow_id=workflow_id,
            error=str(e),
            exc_info=True
        )
        
        # Update workflow status
        if workflow_id in workflow_executions:
            workflow_executions[workflow_id].status = "failed"
            workflow_executions[workflow_id].completed_at = datetime.utcnow()
            workflow_executions[workflow_id].error = str(e)
        
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution failed: {str(e)}"
        )


@router.get("/status/{workflow_id}", response_model=WorkflowStatus)
async def get_workflow_status(
    workflow_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get the status of a workflow execution."""
    if workflow_id not in workflow_executions:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow {workflow_id} not found"
        )
    
    return workflow_executions[workflow_id]


@router.get("/history", response_model=List[WorkflowStatus])
async def get_workflow_history(
    limit: int = 10,
    status: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get workflow execution history.
    
    Args:
        limit: Maximum number of results
        status: Filter by status (pending, running, completed, failed)
    """
    executions = list(workflow_executions.values())
    
    # Filter by status if provided
    if status:
        executions = [e for e in executions if e.status == status]
    
    # Sort by started_at descending
    executions.sort(key=lambda x: x.started_at, reverse=True)
    
    # Limit results
    return executions[:limit]


@router.delete("/clear-history")
async def clear_workflow_history(
    current_user: Dict = Depends(get_current_user)
):
    """Clear workflow execution history (admin only)."""
    workflow_executions.clear()
    
    logger.info(
        "Workflow history cleared",
        user_id=current_user.get("user_id")
    )
    
    return {"success": True, "message": "Workflow history cleared"}
