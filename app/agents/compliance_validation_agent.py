"""Compliance validation agent for checking regulatory compliance."""

from typing import List, Dict, Any

from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.agents.base_agent import BaseAgent, AgentState


class ComplianceIssue(BaseModel):
    """Individual compliance issue."""
    
    regulation: str = Field(description="Regulation or standard violated")
    severity: str = Field(description="Severity: low, medium, high, critical")
    description: str = Field(description="Description of the issue")
    requirement: str = Field(description="Specific requirement not met")
    remediation: str = Field(description="How to remediate the issue")


class ComplianceValidation(BaseModel):
    """Compliance validation result."""
    
    is_compliant: bool = Field(description="Overall compliance status")
    compliance_score: float = Field(description="Compliance score (0-100)")
    
    # Regulatory checks
    hipaa_compliant: bool = Field(description="HIPAA compliance status")
    aca_compliant: bool = Field(description="ACA compliance status")
    state_compliant: bool = Field(description="State regulations compliance")
    coding_standards_compliant: bool = Field(description="Medical coding standards compliance")
    
    # Issues found
    issues: List[ComplianceIssue] = Field(default_factory=list, description="Compliance issues found")
    
    # Specific validations
    privacy_validation: str = Field(description="Privacy and PHI handling validation")
    consent_validation: str = Field(description="Patient consent validation")
    authorization_validation: str = Field(description="Authorization and pre-approval validation")
    documentation_validation: str = Field(description="Documentation requirements validation")
    coding_validation: str = Field(description="Medical coding compliance validation")
    billing_validation: str = Field(description="Billing practices validation")
    
    # Network and contracts
    network_compliance: str = Field(description="Network participation compliance")
    contract_compliance: str = Field(description="Contract terms compliance")
    
    # Recommendations
    critical_actions: List[str] = Field(default_factory=list, description="Critical actions required")
    recommended_improvements: List[str] = Field(default_factory=list, description="Recommended improvements")
    
    # Summary
    validation_summary: str = Field(description="Summary of compliance validation")
    risk_assessment: str = Field(description="Risk assessment for non-compliance")
    confidence: float = Field(description="Confidence in validation (0-1)")


class ComplianceValidationAgent(BaseAgent):
    """Agent for validating regulatory compliance."""

    def __init__(self):
        super().__init__(
            name="compliance_validation",
            description="Validates compliance with healthcare and insurance regulations",
        )
        self.parser = PydanticOutputParser(pydantic_object=ComplianceValidation)

    def create_prompt(self) -> ChatPromptTemplate:
        """Create compliance validation prompt."""
        template = """You are an expert compliance officer specializing in healthcare and insurance regulations.

Validate compliance for the following claim/policy/transaction:

Data to Validate:
{data}

Document Type: {document_type}

Instructions - Check compliance with these regulations:

1. HIPAA (Health Insurance Portability and Accountability Act):
   - Privacy Rule compliance
   - Security Rule compliance
   - Breach notification requirements
   - PHI handling and disclosure
   - Minimum necessary standard
   - Authorization and consent
   - Business associate agreements

2. ACA (Affordable Care Act):
   - Essential health benefits coverage
   - Pre-existing condition protections
   - Lifetime/annual limits prohibited
   - Preventive care coverage
   - Medical loss ratio requirements
   - Grace periods and notifications

3. STATE REGULATIONS:
   - State-specific insurance laws
   - Licensing requirements
   - Mandated benefits
   - Network adequacy
   - Surprise billing protections
   - Balance billing restrictions

4. MEDICAL CODING STANDARDS:
   - ICD-10-CM/PCS compliance
   - CPT/HCPCS coding accuracy
   - Modifier usage correctness
   - Bundling/unbundling rules
   - Code pairing requirements
   - Documentation support

5. BILLING PRACTICES:
   - Clean Claims Act compliance
   - Prompt payment laws
   - EOB requirements
   - Balance billing rules
   - Coordination of benefits
   - Timely filing deadlines

6. DOCUMENTATION:
   - Medical necessity documentation
   - Prior authorization documentation
   - Consent forms
   - Assignment of benefits
   - Release of information

7. ANTI-FRAUD:
   - False Claims Act compliance
   - Anti-Kickback Statute
   - Stark Law (self-referral)
   - Whistleblower protections

For each compliance issue:
- Identify the specific regulation
- Classify severity (low, medium, high, critical)
- Explain the requirement and violation
- Provide remediation steps

Calculate compliance score (0-100):
- 100: Fully compliant
- 80-99: Minor issues
- 60-79: Moderate issues
- 40-59: Significant issues
- 0-39: Major non-compliance

Provide critical actions and recommendations.

{format_instructions}
"""
        return ChatPromptTemplate.from_template(template).partial(
            format_instructions=self.parser.get_format_instructions()
        )

    async def process(self, state: AgentState) -> AgentState:
        """Validate compliance."""
        if not state.text and not state.extracted_entities:
            state.errors.append("No data provided for compliance validation")
            return state

        try:
            # Prepare data for validation
            data = state.extracted_entities or {"raw_text": state.text}
            document_type = state.document_type or "unknown"

            # Create chain
            prompt = self.create_prompt()
            chain = prompt | self.llm | self.parser

            # Run compliance validation
            result: ComplianceValidation = chain.invoke({
                "data": str(data),
                "document_type": document_type,
            })

            # Update state
            state.analysis["compliance"] = {
                "is_compliant": result.is_compliant,
                "compliance_score": result.compliance_score,
                "hipaa_compliant": result.hipaa_compliant,
                "aca_compliant": result.aca_compliant,
                "state_compliant": result.state_compliant,
                "coding_standards_compliant": result.coding_standards_compliant,
                "issues": [issue.dict() for issue in result.issues],
                "privacy_validation": result.privacy_validation,
                "consent_validation": result.consent_validation,
                "authorization_validation": result.authorization_validation,
                "documentation_validation": result.documentation_validation,
                "coding_validation": result.coding_validation,
                "billing_validation": result.billing_validation,
                "network_compliance": result.network_compliance,
                "contract_compliance": result.contract_compliance,
                "critical_actions": result.critical_actions,
                "recommended_improvements": result.recommended_improvements,
                "validation_summary": result.validation_summary,
                "risk_assessment": result.risk_assessment,
                "confidence": result.confidence,
            }
            
            state.confidence = result.confidence
            state.current_step = "compliance_validated"
            state.iterations += 1

            self.logger.info(
                "Compliance validation completed",
                is_compliant=result.is_compliant,
                compliance_score=result.compliance_score,
                issues=len(result.issues),
            )

            # Log critical compliance issues
            if result.compliance_score < 60:
                self.logger.warning(
                    "Significant compliance issues detected",
                    compliance_score=result.compliance_score,
                    critical_issues=[
                        issue.regulation for issue in result.issues 
                        if issue.severity in ["high", "critical"]
                    ],
                )

            return state

        except Exception as e:
            self.logger.error("Compliance validation failed", error=str(e), exc_info=True)
            state.errors.append(f"Compliance validation error: {str(e)}")
            return state
