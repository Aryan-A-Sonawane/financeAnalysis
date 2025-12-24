"""Graph extraction service for building knowledge graphs from documents."""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


# Pydantic models for structured extraction
class Entity(BaseModel):
    """Extracted entity from document."""
    name: str = Field(..., description="Entity name/value")
    type: str = Field(..., description="Entity type (person, organization, policy, claim, diagnosis, etc.)")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional entity properties")
    confidence: float = Field(default=1.0, description="Extraction confidence 0-1")


class Relationship(BaseModel):
    """Relationship between two entities."""
    source: str = Field(..., description="Source entity name")
    target: str = Field(..., description="Target entity name")
    type: str = Field(..., description="Relationship type (covers, claims, diagnoses, treats, etc.)")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Relationship properties")
    confidence: float = Field(default=1.0, description="Extraction confidence 0-1")


class GraphExtraction(BaseModel):
    """Complete graph extraction result."""
    entities: List[Entity] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)


class GraphExtractionService:
    """Service for extracting knowledge graph from documents."""
    
    def __init__(self):
        """Initialize graph extraction service."""
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            max_tokens=3000
        )
        logger.info("Graph extraction service initialized")
    
    def extract_entities_and_relationships(
        self,
        text: str,
        document_type: str,
        document_id: str
    ) -> GraphExtraction:
        """
        Extract entities and relationships from text.
        
        Args:
            text: Document text
            document_type: Type of document
            document_id: Document identifier
            
        Returns:
            GraphExtraction with entities and relationships
        """
        try:
            # Create domain-specific extraction prompt
            prompt = self._create_extraction_prompt(document_type)
            
            # Extract using LLM
            messages = prompt.format_messages(
                document_type=document_type,
                text=text[:8000]  # Limit context
            )
            
            response = self.llm.invoke(messages)
            
            # Parse JSON response
            try:
                result_data = json.loads(response.content)
                extraction = GraphExtraction(**result_data)
            except json.JSONDecodeError:
                logger.warning(
                    "Failed to parse LLM response as JSON",
                    document_id=document_id
                )
                # Fallback: use rule-based extraction
                extraction = self._rule_based_extraction(text, document_type)
            
            logger.info(
                "Graph extraction completed",
                document_id=document_id,
                entity_count=len(extraction.entities),
                relationship_count=len(extraction.relationships)
            )
            
            return extraction
            
        except Exception as e:
            logger.error(
                "Graph extraction failed",
                document_id=document_id,
                error=str(e),
                exc_info=True
            )
            return GraphExtraction()
    
    def _create_extraction_prompt(self, document_type: str) -> ChatPromptTemplate:
        """Create extraction prompt based on document type."""
        
        if document_type == "policy":
            entity_types = "Insurance Policy, Insurance Company, Policy Holder, Coverage, Beneficiary, Network Provider"
            relationship_types = "covers, insures, benefits, excludes, requires"
            
        elif document_type in ["claim_form", "eob"]:
            entity_types = "Claim, Patient, Provider, Diagnosis (ICD-10), Procedure (CPT), Insurance Company, Service Date"
            relationship_types = "claims, diagnoses, performs, treats, pays_for, covers"
            
        elif document_type == "invoice":
            entity_types = "Invoice, Provider, Patient, Service, Medical Code (CPT/HCPCS), Amount"
            relationship_types = "bills, provides, charges, includes"
            
        else:
            entity_types = "Person, Organization, Document, Service, Amount, Date"
            relationship_types = "relates_to, contains, references"
        
        template = """You are an expert at extracting structured knowledge graphs from {document_type} documents.

Extract all relevant entities and relationships from the following text.

**Entity Types to Extract**: {entity_types}
**Relationship Types**: {relationship_types}

**Text**:
{text}

Return a JSON object with this exact structure:
{{
  "entities": [
    {{
      "name": "entity name",
      "type": "entity type",
      "properties": {{}},
      "confidence": 0.95
    }}
  ],
  "relationships": [
    {{
      "source": "source entity name",
      "target": "target entity name",
      "type": "relationship type",
      "properties": {{}},
      "confidence": 0.9
    }}
  ]
}}

Guidelines:
1. Extract all significant entities mentioned in the text
2. Include properties like amounts, dates, codes where relevant
3. Create relationships that capture the document's meaning
4. Use standardized entity/relationship types
5. Set confidence based on extraction certainty

Return only valid JSON, no additional text."""

        return ChatPromptTemplate.from_messages([
            ("system", template)
        ]).partial(
            entity_types=entity_types,
            relationship_types=relationship_types
        )
    
    def _rule_based_extraction(
        self,
        text: str,
        document_type: str
    ) -> GraphExtraction:
        """
        Fallback rule-based extraction when LLM fails.
        
        Args:
            text: Document text
            document_type: Document type
            
        Returns:
            GraphExtraction with basic entities
        """
        entities = []
        relationships = []
        
        # Extract dates
        import re
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
        dates = re.findall(date_pattern, text)
        for date in set(dates):
            entities.append(Entity(
                name=date,
                type="date",
                confidence=0.8
            ))
        
        # Extract amounts
        amount_pattern = r'\$[\d,]+\.?\d*'
        amounts = re.findall(amount_pattern, text)
        for amount in set(amounts):
            entities.append(Entity(
                name=amount,
                type="amount",
                confidence=0.8
            ))
        
        # Extract medical codes (CPT)
        cpt_pattern = r'\b\d{5}\b'
        cpts = re.findall(cpt_pattern, text)
        for cpt in set(cpts):
            entities.append(Entity(
                name=cpt,
                type="procedure_code",
                properties={"code_type": "CPT"},
                confidence=0.7
            ))
        
        # Extract ICD codes
        icd_pattern = r'\b[A-Z]\d{2}\.?\d*\b'
        icds = re.findall(icd_pattern, text)
        for icd in set(icds):
            entities.append(Entity(
                name=icd,
                type="diagnosis_code",
                properties={"code_type": "ICD-10"},
                confidence=0.7
            ))
        
        logger.info(
            "Rule-based extraction completed",
            entity_count=len(entities),
            relationship_count=len(relationships)
        )
        
        return GraphExtraction(
            entities=entities,
            relationships=relationships
        )
    
    def extract_insurance_graph(
        self,
        policy_text: str,
        claim_text: Optional[str] = None
    ) -> GraphExtraction:
        """
        Extract insurance-specific graph.
        
        Args:
            policy_text: Insurance policy document text
            claim_text: Optional claim document text
            
        Returns:
            GraphExtraction with insurance entities/relationships
        """
        try:
            # Extract from policy
            policy_graph = self.extract_entities_and_relationships(
                text=policy_text,
                document_type="policy",
                document_id="temp_policy"
            )
            
            # Extract from claim if provided
            if claim_text:
                claim_graph = self.extract_entities_and_relationships(
                    text=claim_text,
                    document_type="claim_form",
                    document_id="temp_claim"
                )
                
                # Merge graphs
                all_entities = policy_graph.entities + claim_graph.entities
                all_relationships = policy_graph.relationships + claim_graph.relationships
                
                # Add cross-document relationships
                # E.g., link claim to policy
                all_relationships.append(Relationship(
                    source="claim",
                    target="policy",
                    type="covered_by",
                    confidence=0.9
                ))
                
                return GraphExtraction(
                    entities=all_entities,
                    relationships=all_relationships
                )
            
            return policy_graph
            
        except Exception as e:
            logger.error(
                "Insurance graph extraction failed",
                error=str(e),
                exc_info=True
            )
            return GraphExtraction()
    
    def extract_clinical_graph(self, text: str) -> GraphExtraction:
        """
        Extract clinical/medical graph from text.
        
        Args:
            text: Clinical document text
            
        Returns:
            GraphExtraction with medical entities/relationships
        """
        try:
            extraction = self.extract_entities_and_relationships(
                text=text,
                document_type="claim_form",
                document_id="temp_clinical"
            )
            
            # Enhance with clinical relationships
            # E.g., link diagnoses to procedures, procedures to providers
            
            logger.info(
                "Clinical graph extraction completed",
                entity_count=len(extraction.entities),
                relationship_count=len(extraction.relationships)
            )
            
            return extraction
            
        except Exception as e:
            logger.error(
                "Clinical graph extraction failed",
                error=str(e),
                exc_info=True
            )
            return GraphExtraction()
    
    def merge_graphs(
        self,
        graphs: List[GraphExtraction]
    ) -> GraphExtraction:
        """
        Merge multiple graph extractions.
        
        Args:
            graphs: List of GraphExtraction objects
            
        Returns:
            Merged GraphExtraction
        """
        try:
            all_entities = []
            all_relationships = []
            
            # Deduplicate entities by name and type
            entity_map = {}
            for graph in graphs:
                for entity in graph.entities:
                    key = f"{entity.name}:{entity.type}"
                    if key not in entity_map:
                        entity_map[key] = entity
                    else:
                        # Keep entity with higher confidence
                        if entity.confidence > entity_map[key].confidence:
                            entity_map[key] = entity
            
            all_entities = list(entity_map.values())
            
            # Deduplicate relationships
            rel_map = {}
            for graph in graphs:
                for rel in graph.relationships:
                    key = f"{rel.source}:{rel.type}:{rel.target}"
                    if key not in rel_map:
                        rel_map[key] = rel
                    else:
                        if rel.confidence > rel_map[key].confidence:
                            rel_map[key] = rel
            
            all_relationships = list(rel_map.values())
            
            logger.info(
                "Graphs merged",
                input_graphs=len(graphs),
                total_entities=len(all_entities),
                total_relationships=len(all_relationships)
            )
            
            return GraphExtraction(
                entities=all_entities,
                relationships=all_relationships
            )
            
        except Exception as e:
            logger.error(
                "Graph merge failed",
                error=str(e),
                exc_info=True
            )
            return GraphExtraction()


# Singleton instance
_graph_extraction_service: Optional[GraphExtractionService] = None


def get_graph_extraction_service() -> GraphExtractionService:
    """
    Get or create graph extraction service instance.
    
    Returns:
        GraphExtractionService instance
    """
    global _graph_extraction_service
    
    if _graph_extraction_service is None:
        _graph_extraction_service = GraphExtractionService()
    
    return _graph_extraction_service
