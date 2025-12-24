"""Vector store service for Weaviate integration."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from app.db.weaviate import get_weaviate_client
from app.services.embedding_service import get_embedding_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VectorStoreService:
    """Service for managing document vectors in Weaviate."""
    
    def __init__(self):
        """Initialize vector store service."""
        self.client = get_weaviate_client()
        self.embedding_service = get_embedding_service()
        logger.info("Vector store service initialized")
    
    async def store_document(
        self,
        document_id: str,
        text: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Store a document in vector database.
        
        Args:
            document_id: Unique document identifier
            text: Document text content
            metadata: Document metadata (type, user_id, filename, etc.)
            
        Returns:
            Weaviate object UUID
        """
        try:
            # Generate embedding
            embedding = self.embedding_service.generate_embedding(text)
            
            # Prepare document object
            doc_object = {
                "document_id": document_id,
                "content": text[:10000],  # Limit content size
                "document_type": metadata.get("document_type", "unknown"),
                "user_id": metadata.get("user_id", ""),
                "filename": metadata.get("filename", ""),
                "upload_date": metadata.get("upload_date", datetime.utcnow().isoformat()),
                "file_size": metadata.get("file_size", 0),
                "classification_confidence": metadata.get("classification_confidence", 0.0)
            }
            
            # Store in Weaviate
            result = await self.client.create_document(
                properties=doc_object,
                vector=embedding
            )
            
            logger.info(
                "Document stored in vector database",
                document_id=document_id,
                weaviate_uuid=result,
                text_length=len(text)
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Failed to store document in vector database",
                document_id=document_id,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def store_document_chunks(
        self,
        document_id: str,
        chunks: List[str],
        metadata: Dict[str, Any]
    ) -> List[str]:
        """
        Store document chunks as separate vectors.
        
        Args:
            document_id: Parent document ID
            chunks: List of text chunks
            metadata: Document metadata
            
        Returns:
            List of Weaviate UUIDs
        """
        try:
            # Generate embeddings for all chunks
            embeddings = self.embedding_service.generate_embeddings(chunks)
            
            uuids = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_object = {
                    "document_id": document_id,
                    "content": chunk,
                    "chunk_index": i,
                    "document_type": metadata.get("document_type", "unknown"),
                    "user_id": metadata.get("user_id", ""),
                    "filename": metadata.get("filename", ""),
                }
                
                result = await self.client.create_chunk(
                    properties=chunk_object,
                    vector=embedding
                )
                
                uuids.append(result)
            
            logger.info(
                "Document chunks stored in vector database",
                document_id=document_id,
                chunk_count=len(chunks),
                total_text_length=sum(len(c) for c in chunks)
            )
            
            return uuids
            
        except Exception as e:
            logger.error(
                "Failed to store document chunks",
                document_id=document_id,
                chunk_count=len(chunks),
                error=str(e),
                exc_info=True
            )
            raise
    
    async def semantic_search(
        self,
        query: str,
        document_type: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 10,
        min_certainty: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search for similar documents.
        
        Args:
            query: Search query text
            document_type: Optional filter by document type
            user_id: Optional filter by user ID
            limit: Maximum number of results
            min_certainty: Minimum similarity threshold (0-1)
            
        Returns:
            List of matching documents with similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.generate_embedding(query)
            
            # Build filter
            filters = {}
            if document_type:
                filters["document_type"] = document_type
            if user_id:
                filters["user_id"] = user_id
            
            # Search Weaviate
            results = await self.client.search_documents(
                query_vector=query_embedding,
                limit=limit,
                filters=filters,
                min_certainty=min_certainty
            )
            
            logger.info(
                "Semantic search completed",
                query_length=len(query),
                result_count=len(results),
                document_type=document_type,
                user_id=user_id
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Semantic search failed",
                query=query[:100],
                error=str(e),
                exc_info=True
            )
            raise
    
    async def search_chunks(
        self,
        query: str,
        document_id: Optional[str] = None,
        limit: int = 5,
        min_certainty: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search document chunks for relevant passages.
        
        Args:
            query: Search query
            document_id: Optional filter by document ID
            limit: Maximum results
            min_certainty: Minimum similarity threshold
            
        Returns:
            List of matching chunks with scores
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.generate_embedding(query)
            
            # Build filter
            filters = {}
            if document_id:
                filters["document_id"] = document_id
            
            # Search chunks
            results = await self.client.search_chunks(
                query_vector=query_embedding,
                limit=limit,
                filters=filters,
                min_certainty=min_certainty
            )
            
            logger.info(
                "Chunk search completed",
                query_length=len(query),
                result_count=len(results),
                document_id=document_id
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Chunk search failed",
                query=query[:100],
                error=str(e),
                exc_info=True
            )
            raise
    
    async def hybrid_search(
        self,
        query: str,
        alpha: float = 0.7,
        document_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search (vector + keyword).
        
        Args:
            query: Search query
            alpha: Weight for vector search (1.0 = pure vector, 0.0 = pure keyword)
            document_type: Optional document type filter
            limit: Maximum results
            
        Returns:
            List of matching documents
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.generate_embedding(query)
            
            # Build filter
            filters = {}
            if document_type:
                filters["document_type"] = document_type
            
            # Hybrid search
            results = await self.client.hybrid_search_documents(
                query_text=query,
                query_vector=query_embedding,
                alpha=alpha,
                limit=limit,
                filters=filters
            )
            
            logger.info(
                "Hybrid search completed",
                query=query[:100],
                alpha=alpha,
                result_count=len(results)
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Hybrid search failed",
                query=query[:100],
                error=str(e),
                exc_info=True
            )
            raise
    
    async def find_similar_documents(
        self,
        document_id: str,
        limit: int = 5,
        min_certainty: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Find documents similar to a given document.
        
        Args:
            document_id: Reference document ID
            limit: Maximum results
            min_certainty: Minimum similarity threshold
            
        Returns:
            List of similar documents
        """
        try:
            # Get document vector
            doc = await self.client.get_document(document_id)
            
            if not doc:
                logger.warning(
                    "Document not found for similarity search",
                    document_id=document_id
                )
                return []
            
            # Extract vector
            doc_vector = doc.get("_vector", [])
            
            if not doc_vector:
                logger.warning(
                    "No vector found for document",
                    document_id=document_id
                )
                return []
            
            # Search for similar
            results = await self.client.search_documents(
                query_vector=doc_vector,
                limit=limit + 1,  # +1 to exclude self
                min_certainty=min_certainty
            )
            
            # Remove the document itself from results
            results = [r for r in results if r.get("document_id") != document_id][:limit]
            
            logger.info(
                "Similar documents found",
                document_id=document_id,
                result_count=len(results)
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Similar document search failed",
                document_id=document_id,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from vector store.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if successful
        """
        try:
            result = await self.client.delete_document(document_id)
            
            logger.info(
                "Document deleted from vector store",
                document_id=document_id,
                success=result
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Failed to delete document from vector store",
                document_id=document_id,
                error=str(e),
                exc_info=True
            )
            return False
    
    async def get_document_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about stored documents.
        
        Args:
            user_id: Optional filter by user ID
            
        Returns:
            Dict with statistics
        """
        try:
            stats = await self.client.get_document_stats(user_id=user_id)
            
            logger.info(
                "Document stats retrieved",
                user_id=user_id,
                total_documents=stats.get("total_documents", 0)
            )
            
            return stats
            
        except Exception as e:
            logger.error(
                "Failed to get document stats",
                user_id=user_id,
                error=str(e),
                exc_info=True
            )
            return {}


# Singleton instance
_vector_store_service: Optional[VectorStoreService] = None


def get_vector_store_service() -> VectorStoreService:
    """
    Get or create vector store service instance.
    
    Returns:
        VectorStoreService instance
    """
    global _vector_store_service
    
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService()
    
    return _vector_store_service
