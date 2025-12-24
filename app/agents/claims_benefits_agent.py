"""Claims and benefits agent for analyzing insurance claims."""

from typing import List, Dict, Any

from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.agents.base_agent import BaseAgent, AgentState


class ClaimAnalysis(BaseModel):
    """Claim analysis result."""
    
    # Claim details
    claim_number: str = Field(description="Claim number")
    policy_number: str = Field(description="Associated policy number")
    claimant_name: str = Field(description="Claimant name")
    date_of_service: str = Field(description="Date of service")
    provider_name: str = Field(description="Provider name")
    
    # Medical codes
    diagnosis_codes: List[str] = Field(default_factory=list, description="ICD-10 diagnosis codes")
    procedure_codes: List[str] = Field(default_factory=list, description="CPT/HCPCS procedure codes")
    
    # Financial breakdown
    total_charged: float = Field(description="Total amount charged")
    insurance_paid: float = Field(default=0.0, description="Amount paid by insurance")
    patient_responsibility: float = Field(default=0.0, description="Patient responsibility")
    deductible_applied: float = Field(default=0.0, description="Deductible applied")
    coinsurance_applied: float = Field(default=0.0, description="Coinsurance applied")
    copay_applied: float = Field(default=0.0, description="Copay applied")
    
    # Status
    claim_status: str = Field(description="Claim status (pending, approved, denied, etc.)")
    denial_reason: str = Field(default="", description="Reason for denial if applicable")
    
    # Analysis
    coverage_analysis: str = Field(description="Analysis of coverage applicability")
    benefit_calculation: str = Field(description="Explanation of benefit calculations")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for claimant")


class ClaimsAndBenefitsAgent(BaseAgent):
    """Agent for analyzing insurance claims and benefits."""

    def __init__(self):
        super().__init__(
            name="claims_benefits",
            description="Analyzes insurance claims and calculates benefits",
        )
        self.parser = PydanticOutputParser(pydantic_object=ClaimAnalysis)

    def create_prompt(self) -> ChatPromptTemplate:
        """Create claims analysis prompt."""
        template = """You are an expert at analyzing insurance claims and calculating benefits.

Analyze this claim document:

{text}

Instructions:
1. Extract claim identification (claim number, policy number, claimant)
2. Extract service details (date, provider, diagnosis, procedures)
3. Identify all medical codes (ICD-10, CPT, HCPCS)
4. Break down financial components:
   - Total charged by provider
   - Amount paid by insurance
   - Patient responsibility
   - Deductible, coinsurance, copay applied
5. Determine claim status (pending, approved, denied, partial)
6. If denied, extract the denial reason
7. Analyze coverage:
   - Were services covered under the policy?
   - Were medical necessity requirements met?
   - Were there any exclusions or limitations?
8. Explain benefit calculations:
   - How was the allowed amount determined?
   - How was patient responsibility calculated?
9. Provide recommendations:
   - Next steps for the claimant
   - Appeal opportunities if denied
   - Payment arrangements if needed

{format_instructions}
"""
        return ChatPromptTemplate.from_template(template).partial(
            format_instructions=self.parser.get_format_instructions()
        )

    async def process(self, state: AgentState) -> AgentState:
        """Analyze claim."""
        if not state.text:
            state.errors.append("No text provided for claims analysis")
            return state

        try:
            # Create chain
            prompt = self.create_prompt()
            chain = prompt | self.llm | self.parser

            # Run analysis
            result: ClaimAnalysis = chain.invoke({"text": state.text})

            # Update state
            state.extracted_entities = {
                "claim_number": result.claim_number,
                "policy_number": result.policy_number,
                "claimant_name": result.claimant_name,
                "date_of_service": result.date_of_service,
                "provider_name": result.provider_name,
                "diagnosis_codes": result.diagnosis_codes,
                "procedure_codes": result.procedure_codes,
                "total_charged": result.total_charged,
                "insurance_paid": result.insurance_paid,
                "patient_responsibility": result.patient_responsibility,
                "deductible_applied": result.deductible_applied,
                "coinsurance_applied": result.coinsurance_applied,
                "copay_applied": result.copay_applied,
                "claim_status": result.claim_status,
                "denial_reason": result.denial_reason,
            }
            
            state.analysis = {
                "coverage_analysis": result.coverage_analysis,
                "benefit_calculation": result.benefit_calculation,
                "recommendations": result.recommendations,
            }
            
            # Calculate confidence
            required_fields = [
                result.claim_number,
                result.diagnosis_codes,
                result.procedure_codes,
                result.coverage_analysis,
            ]
            state.confidence = sum(1 for f in required_fields if f) / len(required_fields)
            
            state.current_step = "claim_analyzed"
            state.iterations += 1

            self.logger.info(
                "Claim analyzed",
                claim_number=result.claim_number,
                status=result.claim_status,
                total_charged=result.total_charged,
            )

            return state

        except Exception as e:
            self.logger.error("Claims analysis failed", error=str(e), exc_info=True)
            state.errors.append(f"Claims analysis error: {str(e)}")
            return state
