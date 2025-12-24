"""Fraud detection agent for identifying potential fraud patterns."""

from typing import List, Dict, Any

from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.agents.base_agent import BaseAgent, AgentState


class FraudIndicator(BaseModel):
    """Individual fraud indicator."""
    
    indicator_type: str = Field(description="Type of fraud indicator")
    severity: str = Field(description="Severity: low, medium, high, critical")
    description: str = Field(description="Description of the indicator")
    evidence: str = Field(description="Supporting evidence")


class FraudAnalysis(BaseModel):
    """Fraud detection analysis result."""
    
    fraud_risk_score: float = Field(description="Overall fraud risk score (0-100)")
    risk_level: str = Field(description="Risk level: none, low, medium, high, critical")
    
    # Indicators
    indicators: List[FraudIndicator] = Field(default_factory=list, description="Detected fraud indicators")
    
    # Pattern analysis
    billing_patterns: str = Field(description="Analysis of billing patterns")
    coding_patterns: str = Field(description="Analysis of medical coding patterns")
    temporal_patterns: str = Field(description="Analysis of temporal patterns")
    provider_patterns: str = Field(description="Analysis of provider behavior patterns")
    
    # Specific checks
    duplicate_claims: List[str] = Field(default_factory=list, description="Potential duplicate claims")
    upcoding_risks: List[str] = Field(default_factory=list, description="Potential upcoding instances")
    unbundling_risks: List[str] = Field(default_factory=list, description="Potential unbundling instances")
    medical_necessity_issues: List[str] = Field(default_factory=list, description="Medical necessity concerns")
    
    # Recommendations
    investigation_recommended: bool = Field(description="Whether further investigation is recommended")
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended actions")
    review_priorities: List[str] = Field(default_factory=list, description="Priority items for review")
    
    # Summary
    analysis_summary: str = Field(description="Summary of fraud analysis")
    confidence: float = Field(description="Confidence in analysis (0-1)")


class FraudDetectionAgent(BaseAgent):
    """Agent for detecting potential fraud in claims and billing."""

    def __init__(self):
        super().__init__(
            name="fraud_detection",
            description="Detects potential fraud patterns in insurance claims and medical billing",
        )
        self.parser = PydanticOutputParser(pydantic_object=FraudAnalysis)

    def create_prompt(self) -> ChatPromptTemplate:
        """Create fraud detection prompt."""
        template = """You are an expert fraud detection analyst specializing in healthcare and insurance fraud.

Analyze the following claim/billing information for potential fraud indicators:

Claim/Billing Data:
{claim_data}

Historical Context (if available):
{historical_context}

Instructions - Analyze for these fraud patterns:

1. BILLING FRAUD:
   - Billing for services not rendered
   - Duplicate billing
   - Phantom billing (nonexistent patients/providers)
   - Balance billing violations
   - Coordination of benefits fraud

2. CODING FRAUD:
   - Upcoding (billing for more expensive service than provided)
   - Unbundling (separating bundled procedures)
   - Modifier misuse
   - Code manipulation
   - DRG creep

3. MEDICAL NECESSITY FRAUD:
   - Services not medically necessary
   - Diagnosis codes don't support procedures
   - Excessive or inappropriate services
   - Experimental procedures billed as standard

4. PROVIDER FRAUD:
   - Kickbacks and referral schemes
   - Self-referral violations
   - Credential misrepresentation
   - License issues

5. TEMPORAL PATTERNS:
   - Unusual billing frequency
   - Timing anomalies
   - Same-day conflicting services
   - Impossible service combinations

6. STATISTICAL ANOMALIES:
   - Outlier billing amounts
   - Unusual service patterns
   - Provider practice pattern deviations

For each indicator found:
- Classify severity (low, medium, high, critical)
- Provide specific evidence
- Explain the pattern

Calculate overall fraud risk score (0-100):
- 0-20: No significant risk
- 21-40: Low risk
- 41-60: Medium risk
- 61-80: High risk
- 81-100: Critical risk

Provide actionable recommendations for investigation or approval.

{format_instructions}
"""
        return ChatPromptTemplate.from_template(template).partial(
            format_instructions=self.parser.get_format_instructions()
        )

    async def process(self, state: AgentState) -> AgentState:
        """Perform fraud detection analysis."""
        if not state.text and not state.extracted_entities:
            state.errors.append("No data provided for fraud detection")
            return state

        try:
            # Prepare claim data
            claim_data = state.extracted_entities or {"raw_text": state.text}
            historical_context = state.analysis.get("historical_data", "No historical context available")

            # Create chain
            prompt = self.create_prompt()
            chain = prompt | self.llm | self.parser

            # Run fraud detection
            result: FraudAnalysis = chain.invoke({
                "claim_data": str(claim_data),
                "historical_context": str(historical_context),
            })

            # Update state
            state.analysis["fraud_detection"] = {
                "fraud_risk_score": result.fraud_risk_score,
                "risk_level": result.risk_level,
                "indicators": [ind.dict() for ind in result.indicators],
                "billing_patterns": result.billing_patterns,
                "coding_patterns": result.coding_patterns,
                "temporal_patterns": result.temporal_patterns,
                "provider_patterns": result.provider_patterns,
                "duplicate_claims": result.duplicate_claims,
                "upcoding_risks": result.upcoding_risks,
                "unbundling_risks": result.unbundling_risks,
                "medical_necessity_issues": result.medical_necessity_issues,
                "investigation_recommended": result.investigation_recommended,
                "recommended_actions": result.recommended_actions,
                "review_priorities": result.review_priorities,
                "analysis_summary": result.analysis_summary,
                "confidence": result.confidence,
            }
            
            state.confidence = result.confidence
            state.current_step = "fraud_analyzed"
            state.iterations += 1

            self.logger.info(
                "Fraud detection completed",
                risk_score=result.fraud_risk_score,
                risk_level=result.risk_level,
                indicators=len(result.indicators),
            )

            # Log high-risk cases
            if result.fraud_risk_score > 60:
                self.logger.warning(
                    "High fraud risk detected",
                    risk_score=result.fraud_risk_score,
                    indicators=[ind.indicator_type for ind in result.indicators],
                )

            return state

        except Exception as e:
            self.logger.error("Fraud detection failed", error=str(e), exc_info=True)
            state.errors.append(f"Fraud detection error: {str(e)}")
            return state
