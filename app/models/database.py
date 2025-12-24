"""SQLAlchemy database models for PostgreSQL."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """User model."""

    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    documents = relationship("Document", back_populates="user")
    eligibility_checks = relationship("EligibilityCheck", back_populates="user")


class Document(Base):
    """Document model."""

    __tablename__ = "documents"

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(BigInteger)
    mime_type = Column(String(100))
    document_type = Column(String(50), index=True)
    upload_date = Column(TIMESTAMP(timezone=True), server_default=func.now())
    processed = Column(Boolean, default=False)
    processing_status = Column(String(50))
    error_message = Column(Text)
    document_metadata = Column(JSONB)
    
    # Extracted content
    extracted_text = Column(Text)
    extracted_entities = Column(JSONB)
    medical_codes = Column(JSONB)
    classification_confidence = Column(Float)

    # Relationships
    user = relationship("User", back_populates="documents")
    processing_jobs = relationship("ProcessingJob", back_populates="document")


class APILog(Base):
    """API request/response log."""

    __tablename__ = "api_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), index=True)
    endpoint = Column(String(255))
    method = Column(String(10))
    request_body = Column(JSONB)
    response_status = Column(Integer)
    response_body = Column(JSONB)
    latency_ms = Column(Integer)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    correlation_id = Column(UUID(as_uuid=True))


class ProcessingJob(Base):
    """Document processing job."""

    __tablename__ = "processing_jobs"

    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id"))
    job_type = Column(String(50))
    status = Column(String(50))
    started_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))
    result = Column(JSONB)
    error_message = Column(Text)

    # Relationships
    document = relationship("Document", back_populates="processing_jobs")


class EligibilityCheck(Base):
    """Eligibility check record."""

    __tablename__ = "eligibility_checks"

    check_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), index=True)
    policy_id = Column(String(255))
    procedure_code = Column(String(50))
    diagnosis_code = Column(String(50))
    result = Column(String(50))
    confidence_score = Column(Integer)  # Store as int (0-10000) for precision
    explanation = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="eligibility_checks")
