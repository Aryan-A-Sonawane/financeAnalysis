"""Document management endpoints."""

from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.postgres import get_db
from app.models.database import Document as DBDocument
from app.models.schemas import DocumentMetadata, DocumentType, SuccessResponse, TokenData
from app.services.storage_service import get_storage_service
from app.services.ocr_service import get_ocr_service
from app.services.document_service import get_document_classifier
from app.services.extraction_service import get_extraction_service
from app.services.vector_store_service import get_vector_store_service
from app.services.graph_extraction_service import get_graph_extraction_service
from app.services.graph_store_service import get_graph_store_service
from app.workflows import DocumentProcessingWorkflow
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/upload", response_model=DocumentMetadata, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: Optional[DocumentType] = None,
    use_workflow: bool = False,
    background_tasks: BackgroundTasks = None,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a document for processing.
    
    Supported formats: PDF, DOCX, JPEG, PNG
    
    Args:
        file: Document file to upload
        document_type: Optional document type (auto-detected if not provided)
        use_workflow: Use LangGraph AI workflow for comprehensive analysis
        current_user: Authenticated user
        db: Database session
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
    storage = get_storage_service()
    file_path = f"documents/{current_user.user_id}/{file.filename}"
    
    # Upload to storage
    storage.upload_file(
        file_content=content,
        object_key=file_path,
        content_type=file.content_type,
        metadata={
            "user_id": str(current_user.user_id),
            "original_filename": file.filename or "unknown",
        },
    )
    
    logger.info("File uploaded to storage", file_path=file_path)
    
    # Extract text using OCR
    ocr = get_ocr_service()
    
    if file.content_type == "application/pdf":
        extracted_text = ocr.extract_text_from_pdf(content)
    elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        extracted_text = ocr.extract_text_from_docx(content)
    else:  # Image
        extracted_text = ocr.extract_text_from_image(content)
    
    logger.info("Text extracted", text_length=len(extracted_text))
    
    # Classify document if type not provided
    if not document_type:
        classifier = get_document_classifier()
        doc_type_str, confidence = classifier.classify(extracted_text)
        
        # Try LLM if confidence is low
        if confidence < 0.7:
            doc_type_str, confidence = classifier.classify_with_llm(extracted_text)
        
        document_type = DocumentType(doc_type_str)
        logger.info("Document classified", doc_type=doc_type_str, confidence=confidence)
    else:
        confidence = 1.0  # User-provided type
    
    # Extract entities
    extractor = get_extraction_service()
    entities = extractor.extract_entities(extracted_text, document_type)
    
    # Extract medical codes if applicable
    medical_codes = None
    if document_type in [DocumentType.CLAIM_FORM, DocumentType.EOB]:
        medical_codes = extractor.extract_medical_codes(extracted_text)
    
    logger.info("Entities extracted", entity_count=len(entities))

    # Create document record
    db_document = DBDocument(
        user_id=current_user.user_id,
        filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type,
        document_type=document_type.value,
        processed=True,
        processing_status="completed",
        extracted_text=extracted_text[:10000],  # Store first 10k chars
        extracted_entities=entities,
        medical_codes=medical_codes,
        classification_confidence=confidence,
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
        doc_type=document_type.value,
        confidence=confidence,
        use_workflow=use_workflow,
    )
    
    # Run LangGraph workflow if requested
    workflow_result = None
    if use_workflow:
        try:
            workflow = DocumentProcessingWorkflow()
            workflow_result = await workflow.process_document(
                document_id=str(db_document.document_id),
                document_text=extracted_text
            )
            
            # Update document with workflow results
            db_document.extracted_entities = workflow_result.get("extraction", {})
            db_document.processing_status = "workflow_completed"
            
            await db.commit()
            
            logger.info(
                "workflow_completed",
                document_id=str(db_document.document_id),
                success=workflow_result.get("success")
            )
        except Exception as e:
            logger.error(
                "workflow_failed",
                document_id=str(db_document.document_id),
                error=str(e),
                exc_info=True
            )
            # Don't fail the upload if workflow fails
            workflow_result = {"error": str(e)}
    
    # Store in vector database for semantic search
    try:
        vector_store = get_vector_store_service()
        await vector_store.store_document(
            document_id=str(db_document.document_id),
            text=extracted_text,
            metadata={
                "document_type": document_type.value,
                "user_id": str(current_user.user_id),
                "filename": file.filename or "",
                "upload_date": db_document.created_at.isoformat(),
                "file_size": file_size,
                "classification_confidence": confidence
            }
        )
        logger.info(
            "document_stored_in_vector_db",
            document_id=str(db_document.document_id)
        )
    except Exception as e:
        logger.error(
            "vector_store_failed",
            document_id=str(db_document.document_id),
            error=str(e),
            exc_info=True
        )
    
    # Extract and store knowledge graph
    try:
        graph_extractor = get_graph_extraction_service()
        graph_store = get_graph_store_service()
        
        # Extract entities and relationships
        extraction = graph_extractor.extract_entities_and_relationships(
            text=extracted_text,
            document_type=document_type.value,
            document_id=str(db_document.document_id)
        )
        
        # Store in graph database
        graph_result = await graph_store.store_graph(
            document_id=str(db_document.document_id),
            extraction=extraction,
            metadata={
                "document_type": document_type.value,
                "user_id": str(current_user.user_id),
                "filename": file.filename or ""
            }
        )
        
        logger.info(
            "document_stored_in_graph_db",
            document_id=str(db_document.document_id),
            entities=graph_result.get("entities", 0),
            relationships=graph_result.get("relationships", 0)
        )
    except Exception as e:
        logger.error(
            "graph_store_failed",
            document_id=str(db_document.document_id),
            error=str(e),
            exc_info=True
        )
    
    # TODO: Trigger async processing workflow for:
    # - Advanced fraud/eligibility analysis
    
    # Add workflow result to response if available
    response = db_document
    if workflow_result:
        # Store workflow result in a custom attribute
        setattr(response, "_workflow_result", workflow_result)
    
    return response


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
    
    # Delete from S3/MinIO
    storage = get_storage_service()
    try:
        if document.file_path:
            storage.delete_file(document.file_path)
            logger.info("Deleted file from storage", file_path=document.file_path)
    except Exception as e:
        logger.warning("Failed to delete file from storage", error=str(e))
    
    # TODO: Delete from vector store (Weaviate)
    # TODO: Delete from graph database (NebulaGraph)
    
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
