"""Eligibility reasoning agent for determining coverage eligibility."""

from typing import List, Dict, Any

from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.agents.base_agent import BaseAgent, AgentState


class EligibilityDecision(BaseModel):
    """Eligibility determination result."""
    
    is_eligible: bool = Field(description="Whether the service is eligible for coverage")
    confidence: float = Field(description="Confidence in eligibility decision (0-1)")
    coverage_percentage: float = Field(default=0.0, description="Percentage of coverage if eligible")
    
    # Decision factors
    policy_coverage: str = Field(description="Policy coverage assessment")
    medical_necessity: str = Field(description="Medical necessity assessment")
    network_status: str = Field(description="In-network vs out-of-network status")
    
    # Financial calculations
    estimated_cost: float = Field(default=0.0, description="Estimated total cost")
    insurance_payment: float = Field(default=0.0, description="Estimated insurance payment")
    patient_payment: float = Field(default=0.0, description="Estimated patient payment")
    deductible_impact: float = Field(default=0.0, description="Impact on deductible")
    
    # Requirements
    preauth_required: bool = Field(default=False, description="Whether pre-authorization is required")
    documentation_needed: List[str] = Field(default_factory=list, description="Required documentation")
    
    # Reasoning
    decision_reasoning: str = Field(description="Detailed reasoning for eligibility decision")
    coverage_limitations: List[str] = Field(default_factory=list, description="Coverage limitations or restrictions")
    alternatives: List[str] = Field(default_factory=list, description="Alternative covered services if denied")
    next_steps: List[str] = Field(default_factory=list, description="Recommended next steps")


class EligibilityReasoningAgent(BaseAgent):
    """Agent for determining coverage eligibility and reasoning about it."""

    def __init__(self):
        super().__init__(
            name="eligibility_reasoning",
            description="Determines coverage eligibility using policy rules and medical necessity",
        )
        self.parser = PydanticOutputParser(pydantic_object=EligibilityDecision)

    def create_prompt(self) -> ChatPromptTemplate:
        """Create eligibility reasoning prompt."""
        template = """You are an expert at determining insurance coverage eligibility and explaining the reasoning.

Analyze the following information to determine eligibility:

Policy Information:
{policy_info}

Service/Claim Information:
{service_info}

Medical Context:
{medical_context}

Instructions:
1. Determine if the service is eligible for coverage under this policy
2. Assess policy coverage:
   - Is the service type covered?
   - Are there any exclusions that apply?
   - What coverage percentage applies?
3. Assess medical necessity:
   - Is the service medically necessary?
   - Are diagnosis codes appropriate?
   - Are procedure codes appropriate for the diagnosis?
4. Check network status:
   - Is the provider in-network?
   - How does that affect coverage?
5. Calculate financial estimates:
   - Estimated total cost
   - Estimated insurance payment
   - Estimated patient responsibility
   - Impact on deductible and out-of-pocket max
6. Determine requirements:
   - Is pre-authorization needed?
   - What documentation is required?
7. Provide detailed reasoning:
   - Explain your eligibility decision
   - List any coverage limitations
   - Suggest alternatives if not covered
   - Provide clear next steps
8. Be specific about policy clauses and medical coding standards

{format_instructions}
"""
        return ChatPromptTemplate.from_template(template).partial(
            format_instructions=self.parser.get_format_instructions()
        )

    async def process(self, state: AgentState) -> AgentState:
        """Determine eligibility."""
        if not state.text:
            state.errors.append("No information provided for eligibility check")
            return state

        try:
            # Extract policy info from state
            policy_info = state.extracted_entities.get("policy", "No policy information available")
            service_info = state.extracted_entities.get("service", state.text[:2000])
            medical_context = state.extracted_entities.get("medical_codes", "No medical codes available")

            # Create chain
            prompt = self.create_prompt()
            chain = prompt | self.llm | self.parser

            # Run eligibility check
            result: EligibilityDecision = chain.invoke({
                "policy_info": str(policy_info),
                "service_info": str(service_info),
                "medical_context": str(medical_context),
            })

            # Update state
            state.analysis = {
                "is_eligible": result.is_eligible,
                "confidence": result.confidence,
                "coverage_percentage": result.coverage_percentage,
                "policy_coverage": result.policy_coverage,
                "medical_necessity": result.medical_necessity,
                "network_status": result.network_status,
                "estimated_cost": result.estimated_cost,
                "insurance_payment": result.insurance_payment,
                "patient_payment": result.patient_payment,
                "deductible_impact": result.deductible_impact,
                "preauth_required": result.preauth_required,
                "documentation_needed": result.documentation_needed,
                "decision_reasoning": result.decision_reasoning,
                "coverage_limitations": result.coverage_limitations,
                "alternatives": result.alternatives,
                "next_steps": result.next_steps,
            }
            
            state.confidence = result.confidence
            state.current_step = "eligibility_determined"
            state.iterations += 1

            self.logger.info(
                "Eligibility determined",
                is_eligible=result.is_eligible,
                confidence=result.confidence,
                coverage_pct=result.coverage_percentage,
            )

            return state

        except Exception as e:
            self.logger.error("Eligibility reasoning failed", error=str(e), exc_info=True)
            state.errors.append(f"Eligibility reasoning error: {str(e)}")
            return state
