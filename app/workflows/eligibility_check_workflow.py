"""Eligibility check workflow for determining coverage eligibility."""

from typing import Dict, Any
import time

from langgraph.graph import StateGraph, END

from app.agents.base_agent import AgentState
from app.agents.eligibility_reasoning_agent import EligibilityReasoningAgent
from app.agents.fraud_detection_agent import FraudDetectionAgent
from app.agents.compliance_validation_agent import ComplianceValidationAgent
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EligibilityCheckWorkflow:
    """Workflow for checking eligibility with fraud detection and compliance."""

    def __init__(self):
        """Initialize workflow."""
        self.eligibility_agent = EligibilityReasoningAgent()
        self.fraud_detector = FraudDetectionAgent()
        self.compliance_validator = ComplianceValidationAgent()
        
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the workflow graph."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("check_eligibility", self._check_eligibility)
        workflow.add_node("detect_fraud", self._detect_fraud)
        workflow.add_node("validate_compliance", self._validate_compliance)
        
        # Define flow
        workflow.set_entry_point("check_eligibility")
        workflow.add_edge("check_eligibility", "detect_fraud")
        workflow.add_edge("detect_fraud", "validate_compliance")
        workflow.add_edge("validate_compliance", END)
        
        return workflow.compile()

    async def _check_eligibility(self, state: AgentState) -> AgentState:
        """Check eligibility."""
        return await self.eligibility_agent.run(state)

    async def _detect_fraud(self, state: AgentState) -> AgentState:
        """Detect fraud."""
        return await self.fraud_detector.run(state)

    async def _validate_compliance(self, state: AgentState) -> AgentState:
        """Validate compliance."""
        return await self.compliance_validator.run(state)

    async def check_eligibility(
        self,
        policy_info: Dict[str, Any],
        service_info: Dict[str, Any],
        patient_info: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Check eligibility for a service under a policy.
        
        Args:
            policy_info: Policy information
            service_info: Service/procedure information
            patient_info: Optional patient information
            
        Returns:
            Eligibility determination with fraud and compliance checks
        """
        logger.info("Starting eligibility check")
        
        start_time = time.time()
        
        # Prepare text for analysis
        text = f"""
Policy Information:
{self._format_dict(policy_info)}

Service Information:
{self._format_dict(service_info)}

Patient Information:
{self._format_dict(patient_info) if patient_info else 'Not provided'}
"""
        
        # Initialize state
        initial_state = AgentState(
            text=text,
            document_type="eligibility_check",
        )
        
        # Add structured data to state
        initial_state.extracted_entities = {
            "policy": policy_info,
            "service": service_info,
            "patient": patient_info or {},
        }
        
        try:
            # Run workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            processing_time = time.time() - start_time
            
            logger.info(
                "Eligibility check completed",
                is_eligible=final_state.analysis.get("is_eligible"),
                processing_time=processing_time,
            )
            
            return {
                "success": len(final_state.errors) == 0,
                "eligibility": final_state.analysis,
                "fraud_risk": final_state.analysis.get("fraud_detection", {}),
                "compliance": final_state.analysis.get("compliance", {}),
                "confidence": final_state.confidence,
                "processing_time": processing_time,
                "errors": final_state.errors,
            }
            
        except Exception as e:
            logger.error("Eligibility check failed", error=str(e), exc_info=True)
            return {
                "success": False,
                "errors": [str(e)],
                "processing_time": time.time() - start_time,
            }

    def _format_dict(self, data: Dict[str, Any]) -> str:
        """Format dictionary for text representation."""
        if not data:
            return "No data"
        
        lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for k, v in value.items():
                    lines.append(f"  {k}: {v}")
            elif isinstance(value, list):
                lines.append(f"{key}: {', '.join(str(v) for v in value)}")
            else:
                lines.append(f"{key}: {value}")
        
        return "\n".join(lines)


# Global instance
_eligibility_workflow_instance = None


def get_eligibility_check_workflow() -> EligibilityCheckWorkflow:
    """Get or create eligibility workflow instance."""
    global _eligibility_workflow_instance
    if _eligibility_workflow_instance is None:
        _eligibility_workflow_instance = EligibilityCheckWorkflow()
    return _eligibility_workflow_instance
