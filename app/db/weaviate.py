"""Weaviate vector database client."""

from typing import Any, Dict, List, Optional

import weaviate
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.query import MetadataQuery

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WeaviateClient:
    """Weaviate client wrapper."""

    def __init__(self):
        """Initialize Weaviate client."""
        self.client: Optional[weaviate.WeaviateClient] = None

    async def connect(self) -> None:
        """Connect to Weaviate."""
        try:
            # Connect to Weaviate
            if settings.WEAVIATE_API_KEY:
                self.client = weaviate.connect_to_custom(
                    http_host=settings.WEAVIATE_URL.replace("http://", "").replace("https://", ""),
                    http_port=8080,
                    http_secure=False,
                    grpc_host=settings.WEAVIATE_URL.replace("http://", "").replace("https://", ""),
                    grpc_port=50051,
                    grpc_secure=False,
                    auth_credentials=weaviate.auth.AuthApiKey(settings.WEAVIATE_API_KEY)
                )
            else:
                self.client = weaviate.connect_to_local(
                    host=settings.WEAVIATE_URL.replace("http://", "").replace("https://", ""),
                    port=8080
                )

            # Test connection
            if self.client.is_ready():
                logger.info("Weaviate connection established", url=settings.WEAVIATE_URL)
            else:
                raise RuntimeError("Weaviate is not ready")

        except Exception as e:
            logger.error("Failed to connect to Weaviate", error=str(e), exc_info=True)
            raise

    async def close(self) -> None:
        """Close Weaviate connection."""
        if self.client:
            self.client.close()
        logger.info("Weaviate connection closed")

    async def create_schema(self) -> None:
        """Create Weaviate schema."""
        try:
            # DocumentChunk class
            if not self.client.collections.exists("DocumentChunk"):
                self.client.collections.create(
                    name="DocumentChunk",
                    description="Chunked document segments with embeddings",
                    vectorizer_config=Configure.Vectorizer.text2vec_openai(
                        model="text-embedding-3-large"
                    ),
                    properties=[
                        Property(name="content", data_type=DataType.TEXT),
                        Property(name="document_id", data_type=DataType.TEXT),
                        Property(name="document_type", data_type=DataType.TEXT),
                        Property(name="chunk_index", data_type=DataType.INT),
                        Property(name="metadata", data_type=DataType.OBJECT),
                    ]
                )
                logger.info("Created DocumentChunk collection")

            # PolicyClause class
            if not self.client.collections.exists("PolicyClause"):
                self.client.collections.create(
                    name="PolicyClause",
                    description="Extracted policy clauses",
                    vectorizer_config=Configure.Vectorizer.text2vec_openai(
                        model="text-embedding-3-large"
                    ),
                    properties=[
                        Property(name="clause_text", data_type=DataType.TEXT),
                        Property(name="clause_type", data_type=DataType.TEXT),
                        Property(name="policy_id", data_type=DataType.TEXT),
                        Property(name="section", data_type=DataType.TEXT),
                        Property(name="applies_to", data_type=DataType.TEXT_ARRAY),
                        Property(name="extracted_entities", data_type=DataType.OBJECT),
                    ]
                )
                logger.info("Created PolicyClause collection")

            # ClaimRecord class
            if not self.client.collections.exists("ClaimRecord"):
                self.client.collections.create(
                    name="ClaimRecord",
                    description="Historical claim records",
                    vectorizer_config=Configure.Vectorizer.text2vec_openai(
                        model="text-embedding-3-large"
                    ),
                    properties=[
                        Property(name="claim_summary", data_type=DataType.TEXT),
                        Property(name="claim_id", data_type=DataType.TEXT),
                        Property(name="procedure_codes", data_type=DataType.TEXT_ARRAY),
                        Property(name="diagnosis_codes", data_type=DataType.TEXT_ARRAY),
                        Property(name="provider_npi", data_type=DataType.TEXT),
                        Property(name="outcome", data_type=DataType.TEXT),
                        Property(name="approval_confidence", data_type=DataType.NUMBER),
                        Property(name="denial_reason", data_type=DataType.TEXT),
                    ]
                )
                logger.info("Created ClaimRecord collection")

            # InvoiceLineItem class
            if not self.client.collections.exists("InvoiceLineItem"):
                self.client.collections.create(
                    name="InvoiceLineItem",
                    description="Invoice line items",
                    vectorizer_config=Configure.Vectorizer.text2vec_openai(
                        model="text-embedding-3-large"
                    ),
                    properties=[
                        Property(name="description", data_type=DataType.TEXT),
                        Property(name="invoice_id", data_type=DataType.TEXT),
                        Property(name="vendor", data_type=DataType.TEXT),
                        Property(name="amount", data_type=DataType.NUMBER),
                        Property(name="category", data_type=DataType.TEXT),
                    ]
                )
                logger.info("Created InvoiceLineItem collection")

        except Exception as e:
            logger.error("Failed to create Weaviate schema", error=str(e), exc_info=True)
            raise

    async def add_document_chunk(
        self,
        content: str,
        document_id: str,
        document_type: str,
        chunk_index: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add a document chunk."""
        collection = self.client.collections.get("DocumentChunk")
        
        data_object = {
            "content": content,
            "document_id": document_id,
            "document_type": document_type,
            "chunk_index": chunk_index,
            "metadata": metadata or {},
        }
        
        result = collection.data.insert(data_object)
        return str(result)

    async def search_similar_chunks(
        self,
        query: str,
        document_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search for similar document chunks."""
        collection = self.client.collections.get("DocumentChunk")
        
        # Build filter
        filters = None
        if document_type:
            from weaviate.classes.query import Filter
            filters = Filter.by_property("document_type").equal(document_type)
        
        # Execute search
        response = collection.query.near_text(
            query=query,
            limit=limit,
            filters=filters,
            return_metadata=MetadataQuery(distance=True)
        )
        
        results = []
        for obj in response.objects:
            results.append({
                "uuid": str(obj.uuid),
                "content": obj.properties.get("content"),
                "document_id": obj.properties.get("document_id"),
                "metadata": obj.properties.get("metadata"),
                "distance": obj.metadata.distance,
            })
        
        return results

    async def add_claim_record(
        self,
        claim_summary: str,
        claim_id: str,
        procedure_codes: List[str],
        diagnosis_codes: List[str],
        outcome: str,
        **kwargs
    ) -> str:
        """Add a claim record."""
        collection = self.client.collections.get("ClaimRecord")
        
        data_object = {
            "claim_summary": claim_summary,
            "claim_id": claim_id,
            "procedure_codes": procedure_codes,
            "diagnosis_codes": diagnosis_codes,
            "outcome": outcome,
            **kwargs
        }
        
        result = collection.data.insert(data_object)
        return str(result)

    async def find_similar_claims(
        self,
        query: str,
        procedure_code: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find similar historical claims."""
        collection = self.client.collections.get("ClaimRecord")
        
        filters = None
        if procedure_code:
            from weaviate.classes.query import Filter
            filters = Filter.by_property("procedure_codes").contains_any([procedure_code])
        
        response = collection.query.near_text(
            query=query,
            limit=limit,
            filters=filters,
            return_metadata=MetadataQuery(distance=True, certainty=True)
        )
        
        results = []
        for obj in response.objects:
            results.append({
                "uuid": str(obj.uuid),
                "claim_id": obj.properties.get("claim_id"),
                "outcome": obj.properties.get("outcome"),
                "procedure_codes": obj.properties.get("procedure_codes"),
                "diagnosis_codes": obj.properties.get("diagnosis_codes"),
                "distance": obj.metadata.distance,
                "certainty": obj.metadata.certainty,
            })
        
        return results


# Global client instance
weaviate_client = WeaviateClient()


async def get_weaviate_client() -> WeaviateClient:
    """Get Weaviate client instance."""
    if not weaviate_client.client:
        await weaviate_client.connect()
    return weaviate_client
