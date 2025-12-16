"""Document chunking utilities."""

import re
from typing import Any, Dict, List

from app.config import settings


class SemanticChunker:
    """Semantic document chunker with overlap."""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        min_chunk_size: int = None,
    ):
        """Initialize chunker."""
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.min_chunk_size = min_chunk_size or settings.MIN_CHUNK_SIZE

    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Chunk text into semantic segments with overlap.
        
        Args:
            text: Text to chunk
            metadata: Additional metadata to attach to chunks
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        # Split into paragraphs first
        paragraphs = self._split_into_paragraphs(text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_index = 0
        
        for para in paragraphs:
            para_tokens = self._count_tokens(para)
            
            # If paragraph itself is larger than chunk_size, split it
            if para_tokens > self.chunk_size:
                # Save current chunk if any
                if current_chunk:
                    chunks.append(self._create_chunk(
                        current_chunk,
                        chunk_index,
                        metadata
                    ))
                    chunk_index += 1
                    current_chunk = []
                    current_size = 0
                
                # Split large paragraph
                sub_chunks = self._split_large_paragraph(para)
                for sub_chunk in sub_chunks:
                    chunks.append(self._create_chunk(
                        [sub_chunk],
                        chunk_index,
                        metadata
                    ))
                    chunk_index += 1
                
                continue
            
            # Add paragraph to current chunk
            if current_size + para_tokens <= self.chunk_size:
                current_chunk.append(para)
                current_size += para_tokens
            else:
                # Create chunk and start new one
                if current_chunk:
                    chunks.append(self._create_chunk(
                        current_chunk,
                        chunk_index,
                        metadata
                    ))
                    chunk_index += 1
                
                # Handle overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = [overlap_text, para] if overlap_text else [para]
                current_size = self._count_tokens("\n\n".join(current_chunk))
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(self._create_chunk(
                current_chunk,
                chunk_index,
                metadata
            ))
        
        return chunks

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        # Split on double newlines or section markers
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_large_paragraph(self, paragraph: str) -> List[str]:
        """Split a large paragraph into smaller chunks."""
        sentences = re.split(r'[.!?]+\s+', paragraph)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_tokens = self._count_tokens(sentence)
            
            if current_size + sentence_tokens <= self.chunk_size:
                current_chunk.append(sentence)
                current_size += sentence_tokens
            else:
                if current_chunk:
                    chunks.append(". ".join(current_chunk) + ".")
                current_chunk = [sentence]
                current_size = sentence_tokens
        
        if current_chunk:
            chunks.append(". ".join(current_chunk) + ".")
        
        return chunks

    def _get_overlap_text(self, chunks: List[str]) -> str:
        """Get overlap text from previous chunk."""
        if not chunks:
            return ""
        
        combined = "\n\n".join(chunks)
        tokens = combined.split()
        
        if len(tokens) <= self.chunk_overlap:
            return combined
        
        overlap_tokens = tokens[-self.chunk_overlap:]
        return " ".join(overlap_tokens)

    def _count_tokens(self, text: str) -> int:
        """Estimate token count (simple word-based approximation)."""
        # Rough approximation: 1 token ≈ 0.75 words
        words = len(text.split())
        return int(words / 0.75)

    def _create_chunk(
        self,
        paragraphs: List[str],
        index: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create chunk dictionary."""
        content = "\n\n".join(paragraphs)
        
        chunk_metadata = {
            "chunk_index": index,
            "token_count": self._count_tokens(content),
            **(metadata or {}),
        }
        
        return {
            "content": content,
            "metadata": chunk_metadata,
        }


def chunk_document(
    text: str,
    document_id: str,
    document_type: str,
    page_number: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Chunk a document with metadata.
    
    Args:
        text: Document text
        document_id: Document identifier
        document_type: Type of document
        page_number: Optional page number
        
    Returns:
        List of chunks with metadata
    """
    chunker = SemanticChunker()
    
    base_metadata = {
        "document_id": document_id,
        "document_type": document_type,
    }
    
    if page_number is not None:
        base_metadata["page_number"] = page_number
    
    chunks = chunker.chunk_text(text, base_metadata)
    
    return chunks
