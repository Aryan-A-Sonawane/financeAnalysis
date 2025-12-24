"""Document classifier agent using LangGraph."""

from typing import Dict, Any

from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.agents.base_agent import BaseAgent, AgentState
from app.models.schemas import DocumentType


class ClassificationResult(BaseModel):
    """Classification result schema."""
    
    document_type: str = Field(description="Type of document (policy, claim_form, invoice, eob, receipt)")
    confidence: float = Field(description="Confidence score 0-1")
    reasoning: str = Field(description="Explanation for classification")
    key_indicators: list[str] = Field(description="Key phrases that led to classification")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DocumentClassifierAgent(BaseAgent):
    """Agent for classifying financial/insurance documents."""

    def __init__(self):
        super().__init__(
            name="document_classifier",
            description="Classifies financial and insurance documents into specific types",
        )
        self.parser = PydanticOutputParser(pydantic_object=ClassificationResult)

    def create_prompt(self) -> ChatPromptTemplate:
        """Create classification prompt."""
        template = """You are an expert at classifying financial and insurance documents.

Analyze the following document and classify it into one of these types:
- policy: Insurance policy documents
- claim_form: Medical/insurance claim forms
- invoice: Medical or service invoices/bills
- eob: Explanation of Benefits (EOB) documents
- receipt: Payment receipts

Document Text:
{text}

Instructions:
1. Identify the document type based on content, structure, and terminology
2. Look for key indicators like policy numbers, claim numbers, invoice amounts, EOB language
3. Provide a confidence score (0-1) for your classification
4. Explain your reasoning
5. List the key phrases that led to your conclusion

{format_instructions}
"""
        return ChatPromptTemplate.from_template(template).partial(
            format_instructions=self.parser.get_format_instructions()
        )

    async def process(self, state: AgentState) -> AgentState:
        """Classify the document."""
        if not state.text:
            state.errors.append("No text provided for classification")
            return state

        try:
            # Create chain
            prompt = self.create_prompt()
            chain = prompt | self.llm | self.parser

            # Run classification
            result: ClassificationResult = chain.invoke({"text": state.text[:5000]})

            # Update state
            state.document_type = result.document_type
            state.confidence = result.confidence
            state.classifications = {
                "document_type": result.document_type,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "key_indicators": result.key_indicators,
                "metadata": result.metadata,
            }
            state.current_step = "classified"
            state.iterations += 1

            self.logger.info(
                "Document classified",
                document_type=result.document_type,
                confidence=result.confidence,
            )

            return state

        except Exception as e:
            self.logger.error("Classification failed", error=str(e), exc_info=True)
            state.errors.append(f"Classification error: {str(e)}")
            return state
