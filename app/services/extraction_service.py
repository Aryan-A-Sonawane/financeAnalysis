"""Entity extraction service using LLM for structured data extraction."""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.config import settings
from app.models.schemas import DocumentType
from app.utils.logger import get_logger

logger = get_logger(__name__)


# Pydantic models for structured extraction
class PolicyEntity(BaseModel):
    """Extracted policy entity."""
    
    policy_number: Optional[str] = Field(None, description="Policy number")
    policy_holder_name: Optional[str] = Field(None, description="Name of policy holder")
    insurance_company: Optional[str] = Field(None, description="Insurance company name")
    policy_type: Optional[str] = Field(None, description="Type of policy (health, auto, life, etc.)")
    effective_date: Optional[str] = Field(None, description="Policy effective date")
    expiration_date: Optional[str] = Field(None, description="Policy expiration date")
    premium_amount: Optional[float] = Field(None, description="Premium amount")
    coverage_amount: Optional[float] = Field(None, description="Coverage/limit amount")
    deductible: Optional[float] = Field(None, description="Deductible amount")
    copay: Optional[float] = Field(None, description="Copay amount")
    coinsurance: Optional[float] = Field(None, description="Coinsurance percentage")
    covered_services: Optional[List[str]] = Field(default_factory=list, description="List of covered services")
    exclusions: Optional[List[str]] = Field(default_factory=list, description="List of exclusions")
    beneficiaries: Optional[List[str]] = Field(default_factory=list, description="List of beneficiaries")


class ClaimEntity(BaseModel):
    """Extracted claim entity."""
    
    claim_number: Optional[str] = Field(None, description="Claim number")
    policy_number: Optional[str] = Field(None, description="Associated policy number")
    claimant_name: Optional[str] = Field(None, description="Name of claimant")
    date_of_service: Optional[str] = Field(None, description="Date of service")
    date_filed: Optional[str] = Field(None, description="Date claim filed")
    provider_name: Optional[str] = Field(None, description="Healthcare provider name")
    provider_npi: Optional[str] = Field(None, description="Provider NPI number")
    diagnosis_codes: Optional[List[str]] = Field(default_factory=list, description="ICD-10 diagnosis codes")
    procedure_codes: Optional[List[str]] = Field(default_factory=list, description="CPT/HCPCS procedure codes")
    total_charged: Optional[float] = Field(None, description="Total amount charged")
    insurance_paid: Optional[float] = Field(None, description="Amount paid by insurance")
    patient_responsibility: Optional[float] = Field(None, description="Patient responsibility amount")
    claim_status: Optional[str] = Field(None, description="Claim status (pending, approved, denied)")
    denial_reason: Optional[str] = Field(None, description="Reason for denial if applicable")


class InvoiceEntity(BaseModel):
    """Extracted invoice entity."""
    
    invoice_number: Optional[str] = Field(None, description="Invoice number")
    invoice_date: Optional[str] = Field(None, description="Invoice date")
    due_date: Optional[str] = Field(None, description="Payment due date")
    provider_name: Optional[str] = Field(None, description="Provider/vendor name")
    provider_address: Optional[str] = Field(None, description="Provider address")
    provider_tax_id: Optional[str] = Field(None, description="Provider tax ID")
    patient_name: Optional[str] = Field(None, description="Patient name")
    patient_account: Optional[str] = Field(None, description="Patient account number")
    line_items: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Invoice line items")
    subtotal: Optional[float] = Field(None, description="Subtotal amount")
    tax: Optional[float] = Field(None, description="Tax amount")
    total: Optional[float] = Field(None, description="Total amount")
    amount_paid: Optional[float] = Field(None, description="Amount already paid")
    balance_due: Optional[float] = Field(None, description="Balance due")


class EOBEntity(BaseModel):
    """Extracted Explanation of Benefits entity."""
    
    eob_number: Optional[str] = Field(None, description="EOB number")
    claim_number: Optional[str] = Field(None, description="Associated claim number")
    policy_number: Optional[str] = Field(None, description="Policy number")
    patient_name: Optional[str] = Field(None, description="Patient name")
    provider_name: Optional[str] = Field(None, description="Provider name")
    date_of_service: Optional[str] = Field(None, description="Date of service")
    procedure_description: Optional[str] = Field(None, description="Procedure description")
    billed_amount: Optional[float] = Field(None, description="Amount billed")
    allowed_amount: Optional[float] = Field(None, description="Allowed amount")
    deductible_applied: Optional[float] = Field(None, description="Deductible applied")
    coinsurance_applied: Optional[float] = Field(None, description="Coinsurance applied")
    copay_applied: Optional[float] = Field(None, description="Copay applied")
    insurance_paid: Optional[float] = Field(None, description="Amount paid by insurance")
    patient_responsibility: Optional[float] = Field(None, description="Patient responsibility")
    remarks: Optional[List[str]] = Field(default_factory=list, description="EOB remarks/notes")


class ReceiptEntity(BaseModel):
    """Extracted receipt entity."""
    
    receipt_number: Optional[str] = Field(None, description="Receipt number")
    receipt_date: Optional[str] = Field(None, description="Receipt date")
    merchant_name: Optional[str] = Field(None, description="Merchant/provider name")
    merchant_address: Optional[str] = Field(None, description="Merchant address")
    payment_method: Optional[str] = Field(None, description="Payment method")
    transaction_id: Optional[str] = Field(None, description="Transaction ID")
    items: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Receipt items")
    subtotal: Optional[float] = Field(None, description="Subtotal amount")
    tax: Optional[float] = Field(None, description="Tax amount")
    total: Optional[float] = Field(None, description="Total amount paid")


class ExtractionService:
    """Service for extracting structured entities from documents using LLM."""

    def __init__(self):
        """Initialize extraction service."""
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.0,  # Deterministic for extraction
            openai_api_key=settings.OPENAI_API_KEY,
        )
        
        # Entity type to Pydantic model mapping
        self.entity_models = {
            DocumentType.POLICY: PolicyEntity,
            DocumentType.CLAIM_FORM: ClaimEntity,
            DocumentType.INVOICE: InvoiceEntity,
            DocumentType.EOB: EOBEntity,
            DocumentType.RECEIPT: ReceiptEntity,
        }

    def extract_entities(
        self, 
        text: str, 
        document_type: DocumentType
    ) -> Dict[str, Any]:
        """
        Extract structured entities from document text.
        
        Args:
            text: Document text
            document_type: Type of document
            
        Returns:
            Extracted entities as dictionary
        """
        logger.info("Extracting entities", document_type=document_type.value)
        
        # Get appropriate entity model
        entity_model = self.entity_models.get(document_type)
        if not entity_model:
            logger.warning(
                "No extraction model for document type",
                document_type=document_type.value,
            )
            return {"error": f"No extraction model for {document_type.value}"}
        
        # Create parser
        parser = PydanticOutputParser(pydantic_object=entity_model)
        
        # Create extraction prompt
        prompt = self._create_extraction_prompt(document_type, parser)
        
        try:
            # Run extraction
            chain = prompt | self.llm | parser
            result = chain.invoke({"text": text})
            
            # Convert to dict
            entities = result.dict()
            
            logger.info(
                "Entities extracted successfully",
                document_type=document_type.value,
                entity_count=len([v for v in entities.values() if v]),
            )
            
            return entities
            
        except Exception as e:
            logger.error(
                "Failed to extract entities",
                document_type=document_type.value,
                error=str(e),
                exc_info=True,
            )
            # Fall back to simple extraction
            return self._simple_extraction(text, document_type)

    def _create_extraction_prompt(
        self, 
        document_type: DocumentType,
        parser: PydanticOutputParser
    ) -> ChatPromptTemplate:
        """Create extraction prompt for document type."""
        
        format_instructions = parser.get_format_instructions()
        
        # Document-specific instructions
        type_instructions = {
            DocumentType.POLICY: """
Extract policy information including:
- Policy number, holder name, insurance company
- Policy type (health, auto, life, property, etc.)
- Dates (effective, expiration)
- Financial terms (premium, coverage, deductible, copay, coinsurance)
- Covered services and exclusions
- Beneficiaries if applicable
""",
            DocumentType.CLAIM_FORM: """
Extract claim information including:
- Claim number and policy number
- Claimant name and provider details
- Service dates and filing date
- Diagnosis codes (ICD-10) and procedure codes (CPT/HCPCS)
- Financial amounts (charged, paid, patient responsibility)
- Claim status and any denial reasons
""",
            DocumentType.INVOICE: """
Extract invoice information including:
- Invoice number and dates (invoice date, due date)
- Provider/vendor details (name, address, tax ID)
- Patient/account information
- Line items with descriptions and amounts
- Financial totals (subtotal, tax, total, balance due)
""",
            DocumentType.EOB: """
Extract EOB information including:
- EOB number, claim number, policy number
- Patient and provider names
- Service date and procedure description
- Financial breakdown (billed, allowed, deductible, coinsurance, copay)
- Insurance paid vs patient responsibility
- Any remarks or notes
""",
            DocumentType.RECEIPT: """
Extract receipt information including:
- Receipt number and date
- Merchant/provider name and address
- Payment method and transaction ID
- Items purchased/services rendered
- Financial totals (subtotal, tax, total)
""",
        }
        
        instruction = type_instructions.get(
            document_type, 
            "Extract all relevant information from the document."
        )
        
        template = """You are an expert at extracting structured information from financial and insurance documents.

{instruction}

Document Text:
{text}

{format_instructions}

Extract all available information accurately. If a field is not present in the document, leave it as null.
For dates, use YYYY-MM-DD format when possible.
For lists (like diagnosis codes or covered services), extract all mentioned items.
"""
        
        return ChatPromptTemplate.from_template(template).partial(
            instruction=instruction,
            format_instructions=format_instructions,
        )

    def _simple_extraction(
        self, 
        text: str, 
        document_type: DocumentType
    ) -> Dict[str, Any]:
        """
        Simple fallback extraction using basic pattern matching.
        
        This is used when LLM extraction fails.
        """
        logger.info("Using simple extraction fallback")
        
        entities = {
            "extraction_method": "simple_fallback",
            "raw_text_length": len(text),
        }
        
        # Simple regex patterns for common fields
        import re
        
        # Policy/claim/invoice numbers
        number_patterns = [
            r"(?:policy|claim|invoice|receipt)\s*(?:number|#)?\s*:?\s*([A-Z0-9\-]+)",
            r"(?:number|#)\s*:?\s*([A-Z0-9\-]{6,})",
        ]
        for pattern in number_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities["document_number"] = match.group(1)
                break
        
        # Dates
        date_patterns = [
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"(\d{4}[/-]\d{1,2}[/-]\d{1,2})",
        ]
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text))
        if dates:
            entities["dates_found"] = dates[:5]  # Limit to first 5
        
        # Dollar amounts
        amount_pattern = r"\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)"
        amounts = re.findall(amount_pattern, text)
        if amounts:
            entities["amounts_found"] = [
                float(amt.replace(",", "")) for amt in amounts[:10]
            ]
        
        return entities

    def extract_medical_codes(self, text: str) -> Dict[str, List[str]]:
        """
        Extract medical codes (ICD-10, CPT, HCPCS) from text.
        
        Args:
            text: Document text
            
        Returns:
            Dictionary with code types and extracted codes
        """
        import re
        
        codes = {
            "icd10": [],
            "cpt": [],
            "hcpcs": [],
        }
        
        # ICD-10 pattern (e.g., M25.511, Z79.01)
        icd10_pattern = r"\b[A-Z]\d{2}(?:\.\d{1,4})?\b"
        codes["icd10"] = list(set(re.findall(icd10_pattern, text)))
        
        # CPT pattern (5 digits, e.g., 99213, 12345)
        cpt_pattern = r"\b\d{5}\b"
        potential_cpt = re.findall(cpt_pattern, text)
        # Filter to valid CPT range (00100-99999)
        codes["cpt"] = [
            code for code in set(potential_cpt) 
            if 100 <= int(code) <= 99999
        ]
        
        # HCPCS pattern (letter + 4 digits, e.g., J1234, E0123)
        hcpcs_pattern = r"\b[A-Z]\d{4}\b"
        codes["hcpcs"] = list(set(re.findall(hcpcs_pattern, text)))
        
        logger.info(
            "Extracted medical codes",
            icd10_count=len(codes["icd10"]),
            cpt_count=len(codes["cpt"]),
            hcpcs_count=len(codes["hcpcs"]),
        )
        
        return codes


# Global extraction service instance
extraction_service = ExtractionService()


def get_extraction_service() -> ExtractionService:
    """Get extraction service instance."""
    return extraction_service
