"""Embedding service for generating text embeddings using OpenAI."""

from typing import List, Dict, Any, Optional
import numpy as np
from openai import OpenAI

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self, model: str = "text-embedding-3-small"):
        """
        Initialize embedding service.
        
        Args:
            model: OpenAI embedding model to use
                - text-embedding-3-small: 1536 dimensions, fast and cheap
                - text-embedding-3-large: 3072 dimensions, higher quality
                - text-embedding-ada-002: 1536 dimensions, legacy model
        """
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = model
        self.dimension = 1536 if "small" in model or "ada" in model else 3072
        
        logger.info(
            "Embedding service initialized",
            model=model,
            dimension=self.dimension
        )
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
        """
        try:
            # Clean and truncate text (max 8191 tokens for OpenAI)
            text = text.strip()[:32000]  # Rough estimate: 4 chars per token
            
            if not text:
                logger.warning("Empty text provided for embedding")
                return [0.0] * self.dimension
            
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            
            embedding = response.data[0].embedding
            
            logger.debug(
                "Embedding generated",
                text_length=len(text),
                embedding_dim=len(embedding)
            )
            
            return embedding
            
        except Exception as e:
            logger.error(
                "Embedding generation failed",
                error=str(e),
                text_length=len(text),
                exc_info=True
            )
            raise
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings
        """
        try:
            # Clean and truncate texts
            cleaned_texts = [text.strip()[:32000] for text in texts]
            
            # Remove empty texts and track indices
            valid_texts = []
            valid_indices = []
            for i, text in enumerate(cleaned_texts):
                if text:
                    valid_texts.append(text)
                    valid_indices.append(i)
            
            if not valid_texts:
                logger.warning("No valid texts provided for embedding")
                return [[0.0] * self.dimension] * len(texts)
            
            # Generate embeddings in batch (max 2048 texts per request)
            batch_size = 100
            all_embeddings = []
            
            for i in range(0, len(valid_texts), batch_size):
                batch = valid_texts[i:i + batch_size]
                
                response = self.client.embeddings.create(
                    input=batch,
                    model=self.model
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            
            # Reconstruct full list with zeros for empty texts
            result = [[0.0] * self.dimension] * len(texts)
            for idx, embedding in zip(valid_indices, all_embeddings):
                result[idx] = embedding
            
            logger.info(
                "Batch embeddings generated",
                total_texts=len(texts),
                valid_texts=len(valid_texts),
                batches=len(range(0, len(valid_texts), batch_size))
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Batch embedding generation failed",
                error=str(e),
                text_count=len(texts),
                exc_info=True
            )
            raise
    
    def calculate_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score between -1 and 1
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            return float(similarity)
            
        except Exception as e:
            logger.error(
                "Similarity calculation failed",
                error=str(e),
                exc_info=True
            )
            return 0.0
    
    def find_most_similar(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[List[float]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find most similar embeddings to query.
        
        Args:
            query_embedding: Query embedding
            candidate_embeddings: List of candidate embeddings
            top_k: Number of top results to return
            
        Returns:
            List of dicts with index and similarity score
        """
        try:
            similarities = []
            
            for i, candidate in enumerate(candidate_embeddings):
                similarity = self.calculate_similarity(query_embedding, candidate)
                similarities.append({
                    "index": i,
                    "similarity": similarity
                })
            
            # Sort by similarity descending
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Return top k
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(
                "Most similar search failed",
                error=str(e),
                exc_info=True
            )
            return []
    
    def embed_document_chunks(
        self,
        chunks: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Embed document chunks with metadata.
        
        Args:
            chunks: List of text chunks
            metadata: Optional metadata for each chunk
            
        Returns:
            List of dicts with chunk, embedding, and metadata
        """
        try:
            embeddings = self.generate_embeddings(chunks)
            
            results = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                result = {
                    "chunk": chunk,
                    "embedding": embedding,
                    "chunk_index": i
                }
                
                if metadata and i < len(metadata):
                    result.update(metadata[i])
                
                results.append(result)
            
            logger.info(
                "Document chunks embedded",
                chunk_count=len(chunks),
                has_metadata=metadata is not None
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Document chunk embedding failed",
                error=str(e),
                chunk_count=len(chunks),
                exc_info=True
            )
            raise


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(model: str = "text-embedding-3-small") -> EmbeddingService:
    """
    Get or create embedding service instance.
    
    Args:
        model: OpenAI embedding model to use
        
    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    
    if _embedding_service is None or _embedding_service.model != model:
        _embedding_service = EmbeddingService(model=model)
    
    return _embedding_service
