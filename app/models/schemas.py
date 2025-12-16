"""Pydantic models for API requests and responses."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# Enums
class DocumentType(str, Enum):
    """Document type enumeration."""
    POLICY = "policy"
    CLAIM = "claim"
    INVOICE = "invoice"
    EOB = "eob"
    RECEIPT = "receipt"


class ClaimStatus(str, Enum):
    """Claim status enumeration."""
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    APPROVED = "approved"
    DENIED = "denied"
    PAID = "paid"


class EligibilityResult(str, Enum):
    """Eligibility decision enumeration."""
    APPROVED = "approved"
    CONDITIONALLY_APPROVED = "conditionally_approved"
    DENIED = "denied"
    REQUIRES_INFO = "requires_info"


class PolicyType(str, Enum):
    """Insurance policy type."""
    HMO = "hmo"
    PPO = "ppo"
    EPO = "epo"
    POS = "pos"
    HDHP = "hdhp"


# Base Models
class BaseSchema(BaseModel):
    """Base schema with common configurations."""
    model_config = {"from_attributes": True, "use_enum_values": True}


# Document Models
class DocumentUploadRequest(BaseSchema):
    """Document upload request."""
    document_type: Optional[DocumentType] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentMetadata(BaseSchema):
    """Document metadata."""
    document_id: UUID
    filename: str
    file_size: int
    mime_type: str
    document_type: Optional[DocumentType]
    upload_date: datetime
    processed: bool = False
    processing_status: Optional[str] = None


class DocumentProcessingResponse(BaseSchema):
    """Document processing response."""
    document_id: UUID
    status: str
    extracted_entities: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


# Entity Models
class PolicyEntity(BaseSchema):
    """Extracted policy entity."""
    policy_id: str
    policy_number: str
    policy_type: PolicyType
    carrier: str
    effective_date: date
    expiration_date: date
    premium: Optional[Decimal] = None
    deductible_individual: Optional[Decimal] = None
    deductible_family: Optional[Decimal] = None
    oop_max_individual: Optional[Decimal] = None
    oop_max_family: Optional[Decimal] = None
    coinsurance_rate: Optional[Decimal] = None


class CoverageEntity(BaseSchema):
    """Extracted coverage entity."""
    coverage_id: str
    coverage_type: str
    service_category: str
    copay: Optional[Decimal] = None
    coinsurance: Optional[Decimal] = None
    requires_preauth: bool = False
    annual_limit: Optional[Decimal] = None
    visit_limit: Optional[int] = None


class ProcedureEntity(BaseSchema):
    """Medical procedure entity."""
    cpt_code: str
    hcpcs_code: Optional[str] = None
    description: str
    category: Optional[str] = None


class DiagnosisEntity(BaseSchema):
    """Diagnosis entity."""
    icd10_code: str
    description: str
    is_chronic: bool = False


class ClaimEntity(BaseSchema):
    """Claim entity."""
    claim_id: str
    claim_number: str
    submission_date: date
    service_date: date
    billed_amount: Decimal
    allowed_amount: Optional[Decimal] = None
    paid_amount: Optional[Decimal] = None
    patient_responsibility: Optional[Decimal] = None
    status: ClaimStatus
    denial_reason: Optional[str] = None


# Eligibility Models
class EligibilityCheckRequest(BaseSchema):
    """Claims eligibility check request."""
    user_id: str
    policy_id: str
    procedure_code: str
    diagnosis_code: str
    provider_npi: Optional[str] = None
    service_date: Optional[date] = None
    estimated_cost: Optional[Decimal] = None


class CostEstimate(BaseSchema):
    """Patient cost estimate."""
    deductible_remaining: Decimal
    estimated_copay: Decimal
    estimated_coinsurance: Decimal
    estimated_patient_cost: Decimal
    estimated_insurance_payment: Decimal
    oop_remaining: Decimal


class EligibilityCheckResponse(BaseSchema):
    """Claims eligibility check response."""
    check_id: UUID
    result: EligibilityResult
    confidence_score: float = Field(ge=0.0, le=1.0)
    explanation: str
    cost_estimate: Optional[CostEstimate] = None
    requirements: List[str] = []
    similar_claims: List[Dict[str, Any]] = []
    graph_path: Optional[List[str]] = None


# Fraud Detection Models
class FraudAnalysisRequest(BaseSchema):
    """Fraud analysis request."""
    claim_id: str
    include_provider_history: bool = True
    similarity_threshold: float = Field(default=0.8, ge=0.0, le=1.0)


class FraudIndicator(BaseSchema):
    """Fraud indicator."""
    indicator_type: str
    severity: str  # low, medium, high
    description: str
    evidence: Dict[str, Any]


class FraudAnalysisResponse(BaseSchema):
    """Fraud analysis response."""
    claim_id: str
    fraud_risk_score: float = Field(ge=0.0, le=1.0)
    risk_level: str  # low, medium, high
    indicators: List[FraudIndicator]
    similar_claims: List[Dict[str, Any]]
    recommendation: str


# Policy Query Models
class PolicyCoverageRequest(BaseSchema):
    """Policy coverage query request."""
    policy_id: str
    service_category: Optional[str] = None


class PolicyCoverageResponse(BaseSchema):
    """Policy coverage query response."""
    policy_id: str
    coverages: List[CoverageEntity]
    exclusions: List[Dict[str, Any]]
    limitations: List[Dict[str, Any]]


# Extraction Models
class EntityExtractionRequest(BaseSchema):
    """Entity extraction request."""
    document_id: UUID
    entity_types: Optional[List[str]] = None


class EntityExtractionResponse(BaseSchema):
    """Entity extraction response."""
    document_id: UUID
    entities: Dict[str, List[Any]]
    confidence_scores: Dict[str, float]


# Authentication Models
class Token(BaseSchema):
    """JWT token."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseSchema):
    """Token payload data."""
    user_id: Optional[str] = None
    email: Optional[str] = None


class UserCreate(BaseSchema):
    """User creation request."""
    email: str
    password: str = Field(min_length=12)
    role: str = "user"


class User(BaseSchema):
    """User model."""
    user_id: UUID
    email: str
    role: str
    created_at: datetime


# Generic Response Models
class SuccessResponse(BaseSchema):
    """Generic success response."""
    success: bool = True
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseSchema):
    """Generic error response."""
    success: bool = False
    error: str
    detail: Optional[str] = None
