"""Policy parser agent for extracting insurance policy information."""

from typing import List

from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.agents.base_agent import BaseAgent, AgentState


class Coverage(BaseModel):
    """Coverage detail."""
    
    service: str = Field(description="Covered service or category")
    coverage_percentage: float = Field(default=100.0, description="Coverage percentage")
    copay: float = Field(default=0.0, description="Copay amount")
    notes: str = Field(default="", description="Additional coverage notes")


class PolicyData(BaseModel):
    """Extracted policy data."""
    
    policy_number: str = Field(description="Policy number")
    policy_holder: str = Field(description="Policy holder name")
    insurance_company: str = Field(description="Insurance company name")
    policy_type: str = Field(description="Type of policy (health, auto, life, etc.)")
    effective_date: str = Field(description="Policy effective date")
    expiration_date: str = Field(description="Policy expiration date")
    
    # Financial terms
    premium_amount: float = Field(default=0.0, description="Premium amount")
    deductible: float = Field(default=0.0, description="Deductible amount")
    out_of_pocket_max: float = Field(default=0.0, description="Out-of-pocket maximum")
    coinsurance: float = Field(default=0.0, description="Coinsurance percentage")
    
    # Coverage details
    coverages: List[Coverage] = Field(default_factory=list, description="List of covered services")
    exclusions: List[str] = Field(default_factory=list, description="List of exclusions")
    
    # Additional info
    network_type: str = Field(default="", description="Network type (PPO, HMO, etc.)")
    member_id: str = Field(default="", description="Member ID")
    group_number: str = Field(default="", description="Group number")
    beneficiaries: List[str] = Field(default_factory=list, description="Beneficiaries")


class PolicyParserAgent(BaseAgent):
    """Agent for parsing insurance policy documents."""

    def __init__(self):
        super().__init__(
            name="policy_parser",
            description="Parses insurance policy documents and extracts key information",
        )
        self.parser = PydanticOutputParser(pydantic_object=PolicyData)

    def create_prompt(self) -> ChatPromptTemplate:
        """Create policy parsing prompt."""
        template = """You are an expert at analyzing insurance policy documents.

Extract all relevant information from this insurance policy:

{text}

Instructions:
1. Extract policy identification (number, holder, company, type)
2. Extract dates (effective date, expiration date)
3. Extract financial terms (premium, deductible, out-of-pocket max, coinsurance)
4. List all covered services with their coverage details (percentage, copays)
5. List all exclusions (services not covered)
6. Extract network information (PPO, HMO, EPO, etc.)
7. Extract member/group IDs
8. List beneficiaries if mentioned
9. Use YYYY-MM-DD format for dates
10. Ensure monetary amounts are numeric

{format_instructions}
"""
        return ChatPromptTemplate.from_template(template).partial(
            format_instructions=self.parser.get_format_instructions()
        )

    async def process(self, state: AgentState) -> AgentState:
        """Parse policy document."""
        if not state.text:
            state.errors.append("No text provided for policy parsing")
            return state

        try:
            # Create chain
            prompt = self.create_prompt()
            chain = prompt | self.llm | self.parser

            # Run parsing
            result: PolicyData = chain.invoke({"text": state.text})

            # Update state
            state.extracted_entities = {
                "policy_number": result.policy_number,
                "policy_holder": result.policy_holder,
                "insurance_company": result.insurance_company,
                "policy_type": result.policy_type,
                "effective_date": result.effective_date,
                "expiration_date": result.expiration_date,
                "premium_amount": result.premium_amount,
                "deductible": result.deductible,
                "out_of_pocket_max": result.out_of_pocket_max,
                "coinsurance": result.coinsurance,
                "coverages": [cov.dict() for cov in result.coverages],
                "exclusions": result.exclusions,
                "network_type": result.network_type,
                "member_id": result.member_id,
                "group_number": result.group_number,
                "beneficiaries": result.beneficiaries,
            }
            
            # Calculate confidence
            required_fields = [
                result.policy_number,
                result.policy_holder,
                result.insurance_company,
                result.coverages,
            ]
            state.confidence = sum(1 for f in required_fields if f) / len(required_fields)
            
            state.current_step = "policy_parsed"
            state.iterations += 1

            self.logger.info(
                "Policy parsed",
                policy_number=result.policy_number,
                coverages=len(result.coverages),
                exclusions=len(result.exclusions),
            )

            return state

        except Exception as e:
            self.logger.error("Policy parsing failed", error=str(e), exc_info=True)
            state.errors.append(f"Policy parsing error: {str(e)}")
            return state
