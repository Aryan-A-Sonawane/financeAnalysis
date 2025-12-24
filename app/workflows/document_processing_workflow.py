"""LangGraph workflow for document processing using multiple agents."""

from typing import Dict, Any, Literal
import time

from langgraph.graph import StateGraph, END

from app.agents.base_agent import AgentState
from app.agents.document_classifier_agent import DocumentClassifierAgent
from app.agents.invoice_extraction_agent import InvoiceExtractionAgent
from app.agents.policy_parser_agent import PolicyParserAgent
from app.agents.claims_benefits_agent import ClaimsAndBenefitsAgent
from app.agents.eligibility_reasoning_agent import EligibilityReasoningAgent
from app.agents.fraud_detection_agent import FraudDetectionAgent
from app.agents.compliance_validation_agent import ComplianceValidationAgent
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentProcessingWorkflow:
    """LangGraph workflow for comprehensive document processing."""

    def __init__(self):
        """Initialize workflow with all agents."""
        self.classifier = DocumentClassifierAgent()
        self.invoice_extractor = InvoiceExtractionAgent()
        self.policy_parser = PolicyParserAgent()
        self.claims_analyzer = ClaimsAndBenefitsAgent()
        self.eligibility_agent = EligibilityReasoningAgent()
        self.fraud_detector = FraudDetectionAgent()
        self.compliance_validator = ComplianceValidationAgent()
        
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("classify", self._classify_document)
        workflow.add_node("extract_invoice", self._extract_invoice)
        workflow.add_node("parse_policy", self._parse_policy)
        workflow.add_node("analyze_claim", self._analyze_claim)
        workflow.add_node("check_eligibility", self._check_eligibility)
        workflow.add_node("detect_fraud", self._detect_fraud)
        workflow.add_node("validate_compliance", self._validate_compliance)
        
        # Set entry point
        workflow.set_entry_point("classify")
        
        # Add conditional edges based on document type
        workflow.add_conditional_edges(
            "classify",
            self._route_after_classification,
            {
                "invoice": "extract_invoice",
                "policy": "parse_policy",
                "claim": "analyze_claim",
                "eob": "analyze_claim",
                "end": END,
            }
        )
        
        # Invoice path
        workflow.add_edge("extract_invoice", "detect_fraud")
        
        # Policy path
        workflow.add_edge("parse_policy", "validate_compliance")
        
        # Claim path
        workflow.add_edge("analyze_claim", "check_eligibility")
        workflow.add_edge("check_eligibility", "detect_fraud")
        
        # All paths converge at fraud detection
        workflow.add_edge("detect_fraud", "validate_compliance")
        
        # Final step
        workflow.add_edge("validate_compliance", END)
        
        return workflow.compile()

    def _route_after_classification(
        self, state: AgentState
    ) -> Literal["invoice", "policy", "claim", "eob", "end"]:
        """Route to appropriate agent based on document type."""
        if state.errors:
            logger.warning("Classification errors, ending workflow", errors=state.errors)
            return "end"
        
        doc_type = state.document_type
        
        if not doc_type:
            logger.warning("No document type determined")
            return "end"
        
        if doc_type == "invoice":
            return "invoice"
        elif doc_type == "policy":
            return "policy"
        elif doc_type in ["claim_form", "claim"]:
            return "claim"
        elif doc_type == "eob":
            return "eob"
        else:
            logger.warning(f"Unknown document type: {doc_type}")
            return "end"

    async def _classify_document(self, state: AgentState) -> AgentState:
        """Classify document type."""
        logger.info("Starting document classification")
        return await self.classifier.run(state)

    async def _extract_invoice(self, state: AgentState) -> AgentState:
        """Extract invoice data."""
        logger.info("Extracting invoice data")
        return await self.invoice_extractor.run(state)

    async def _parse_policy(self, state: AgentState) -> AgentState:
        """Parse policy document."""
        logger.info("Parsing policy document")
        return await self.policy_parser.run(state)

    async def _analyze_claim(self, state: AgentState) -> AgentState:
        """Analyze claim."""
        logger.info("Analyzing claim")
        return await self.claims_analyzer.run(state)

    async def _check_eligibility(self, state: AgentState) -> AgentState:
        """Check eligibility."""
        logger.info("Checking eligibility")
        return await self.eligibility_agent.run(state)

    async def _detect_fraud(self, state: AgentState) -> AgentState:
        """Detect fraud patterns."""
        logger.info("Detecting fraud patterns")
        return await self.fraud_detector.run(state)

    async def _validate_compliance(self, state: AgentState) -> AgentState:
        """Validate compliance."""
        logger.info("Validating compliance")
        return await self.compliance_validator.run(state)

    async def process_document(
        self, 
        text: str, 
        document_id: str = None,
        document_type: str = None,
    ) -> Dict[str, Any]:
        """
        Process a document through the complete workflow.
        
        Args:
            text: Document text
            document_id: Optional document ID
            document_type: Optional pre-determined document type
            
        Returns:
            Processing results
        """
        logger.info(
            "Starting document processing workflow",
            document_id=document_id,
            text_length=len(text),
        )
        
        start_time = time.time()
        
        # Initialize state
        initial_state = AgentState(
            document_id=document_id,
            text=text,
            document_type=document_type,
        )
        
        try:
            # Run workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            processing_time = time.time() - start_time
            final_state.processing_time = processing_time
            
            logger.info(
                "Document processing completed",
                document_id=document_id,
                document_type=final_state.document_type,
                processing_time=processing_time,
                errors=len(final_state.errors),
            )
            
            return {
                "success": len(final_state.errors) == 0,
                "document_id": final_state.document_id,
                "document_type": final_state.document_type,
                "extracted_entities": final_state.extracted_entities,
                "classifications": final_state.classifications,
                "analysis": final_state.analysis,
                "confidence": final_state.confidence,
                "processing_time": final_state.processing_time,
                "errors": final_state.errors,
                "iterations": final_state.iterations,
            }
            
        except Exception as e:
            logger.error(
                "Workflow execution failed",
                document_id=document_id,
                error=str(e),
                exc_info=True,
            )
            return {
                "success": False,
                "document_id": document_id,
                "errors": [str(e)],
                "processing_time": time.time() - start_time,
            }


# Global workflow instance
_workflow_instance = None


def get_document_processing_workflow() -> DocumentProcessingWorkflow:
    """Get or create workflow instance."""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = DocumentProcessingWorkflow()
    return _workflow_instance
