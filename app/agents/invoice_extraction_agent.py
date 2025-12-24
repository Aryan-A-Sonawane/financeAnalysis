"""Invoice extraction agent for extracting structured data from invoices."""

from typing import List, Dict, Any

from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.agents.base_agent import BaseAgent, AgentState


class LineItem(BaseModel):
    """Invoice line item."""
    
    description: str = Field(description="Service or item description")
    code: str = Field(default="", description="Service code (CPT, HCPCS, etc.)")
    quantity: float = Field(default=1.0, description="Quantity")
    unit_price: float = Field(description="Unit price")
    total: float = Field(description="Line total")


class InvoiceData(BaseModel):
    """Extracted invoice data."""
    
    invoice_number: str = Field(description="Invoice number")
    invoice_date: str = Field(description="Invoice date")
    due_date: str = Field(default="", description="Due date")
    provider_name: str = Field(description="Provider/vendor name")
    provider_address: str = Field(default="", description="Provider address")
    provider_tax_id: str = Field(default="", description="Provider tax ID")
    patient_name: str = Field(default="", description="Patient/customer name")
    patient_account: str = Field(default="", description="Account number")
    line_items: List[LineItem] = Field(description="Invoice line items")
    subtotal: float = Field(description="Subtotal amount")
    tax: float = Field(default=0.0, description="Tax amount")
    total: float = Field(description="Total amount")
    balance_due: float = Field(description="Balance due")
    payment_terms: str = Field(default="", description="Payment terms")
    notes: str = Field(default="", description="Additional notes")


class InvoiceExtractionAgent(BaseAgent):
    """Agent for extracting structured data from invoices."""

    def __init__(self):
        super().__init__(
            name="invoice_extractor",
            description="Extracts structured information from medical and service invoices",
        )
        self.parser = PydanticOutputParser(pydantic_object=InvoiceData)

    def create_prompt(self) -> ChatPromptTemplate:
        """Create invoice extraction prompt."""
        template = """You are an expert at extracting structured information from invoices and bills.

Extract all relevant information from this invoice/bill:

{text}

Instructions:
1. Extract invoice header information (number, dates, provider details)
2. Parse all line items with descriptions, codes, quantities, and amounts
3. Calculate or extract totals (subtotal, tax, total, balance due)
4. Extract patient/customer information
5. Include any payment terms or notes
6. For medical invoices, extract procedure codes (CPT/HCPCS) if present
7. Ensure all monetary amounts are numeric (remove $ and commas)
8. Use YYYY-MM-DD format for dates when possible

{format_instructions}
"""
        return ChatPromptTemplate.from_template(template).partial(
            format_instructions=self.parser.get_format_instructions()
        )

    async def process(self, state: AgentState) -> AgentState:
        """Extract invoice data."""
        if not state.text:
            state.errors.append("No text provided for invoice extraction")
            return state

        try:
            # Create chain
            prompt = self.create_prompt()
            chain = prompt | self.llm | self.parser

            # Run extraction
            result: InvoiceData = chain.invoke({"text": state.text})

            # Update state
            state.extracted_entities = {
                "invoice_number": result.invoice_number,
                "invoice_date": result.invoice_date,
                "due_date": result.due_date,
                "provider_name": result.provider_name,
                "provider_address": result.provider_address,
                "provider_tax_id": result.provider_tax_id,
                "patient_name": result.patient_name,
                "patient_account": result.patient_account,
                "line_items": [item.dict() for item in result.line_items],
                "subtotal": result.subtotal,
                "tax": result.tax,
                "total": result.total,
                "balance_due": result.balance_due,
                "payment_terms": result.payment_terms,
                "notes": result.notes,
            }
            
            # Calculate confidence based on completeness
            required_fields = [
                result.invoice_number,
                result.provider_name,
                result.line_items,
            ]
            state.confidence = sum(1 for f in required_fields if f) / len(required_fields)
            
            state.current_step = "invoice_extracted"
            state.iterations += 1

            self.logger.info(
                "Invoice extracted",
                invoice_number=result.invoice_number,
                line_items=len(result.line_items),
                total=result.total,
            )

            return state

        except Exception as e:
            self.logger.error("Invoice extraction failed", error=str(e), exc_info=True)
            state.errors.append(f"Invoice extraction error: {str(e)}")
            return state
