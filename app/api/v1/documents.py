"""Document management endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.postgres import get_db
from app.models.database import Document as DBDocument
from app.models.schemas import DocumentMetadata, DocumentType, SuccessResponse, TokenData
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/upload", response_model=DocumentMetadata, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: Optional[DocumentType] = None,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a document for processing.
    
    Supported formats: PDF, DOCX, JPEG, PNG
    """
    # Validate file size
    from app.config import settings
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB",
        )

    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image/jpeg",
        "image/png",
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}",
        )

    # TODO: Upload to S3/MinIO
    # For now, store file path placeholder
    file_path = f"documents/{current_user.user_id}/{file.filename}"

    # Create document record
    db_document = DBDocument(
        user_id=current_user.user_id,
        filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type,
        document_type=document_type.value if document_type else None,
        processed=False,
        processing_status="uploaded",
    )
    
    db.add(db_document)
    await db.commit()
    await db.refresh(db_document)
    
    logger.info(
        "document_uploaded",
        document_id=str(db_document.document_id),
        user_id=current_user.user_id,
        filename=file.filename,
        file_size=file_size,
    )
    
    # TODO: Trigger async processing workflow
    
    return db_document


@router.get("/{document_id}", response_model=DocumentMetadata)
async def get_document(
    document_id: UUID,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get document metadata."""
    result = await db.execute(
        select(DBDocument).where(
            DBDocument.document_id == document_id,
            DBDocument.user_id == current_user.user_id,
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    return document


@router.delete("/{document_id}", response_model=SuccessResponse)
async def delete_document(
    document_id: UUID,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document."""
    result = await db.execute(
        select(DBDocument).where(
            DBDocument.document_id == document_id,
            DBDocument.user_id == current_user.user_id,
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # TODO: Delete from S3/MinIO
    # TODO: Delete from vector store
    # TODO: Delete from graph database
    
    await db.delete(document)
    await db.commit()
    
    logger.info(
        "document_deleted",
        document_id=str(document_id),
        user_id=current_user.user_id,
    )
    
    return SuccessResponse(message="Document deleted successfully")


@router.get("/", response_model=list[DocumentMetadata])
async def list_documents(
    document_type: Optional[DocumentType] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's documents."""
    query = select(DBDocument).where(DBDocument.user_id == current_user.user_id)
    
    if document_type:
        query = query.where(DBDocument.document_type == document_type.value)
    
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return documents
