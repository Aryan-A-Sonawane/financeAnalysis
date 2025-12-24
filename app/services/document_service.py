"""Document classification service."""

from typing import Dict, Optional

from app.config import settings
from app.models.schemas import DocumentType
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentClassifier:
    """Classify documents based on content and patterns."""

    def __init__(self):
        """Initialize document classifier."""
        # Keywords for each document type
        self.classification_patterns = {
            DocumentType.POLICY: {
                "keywords": [
                    "policy number",
                    "policyholder",
                    "premium",
                    "deductible",
                    "copay",
                    "coinsurance",
                    "coverage",
                    "benefits",
                    "exclusions",
                    "out-of-pocket",
                    "effective date",
                    "insurance carrier",
                ],
                "weight": 1.0,
            },
            DocumentType.CLAIM: {
                "keywords": [
                    "claim number",
                    "claimant",
                    "date of service",
                    "provider",
                    "diagnosis code",
                    "procedure code",
                    "cpt",
                    "icd-10",
                    "billed amount",
                    "allowed amount",
                    "patient responsibility",
                    "claim status",
                ],
                "weight": 1.0,
            },
            DocumentType.EOB: {
                "keywords": [
                    "explanation of benefits",
                    "eob",
                    "service date",
                    "amount charged",
                    "amount allowed",
                    "deductible",
                    "copay",
                    "you may owe",
                    "provider paid",
                    "member id",
                ],
                "weight": 1.0,
            },
            DocumentType.INVOICE: {
                "keywords": [
                    "invoice",
                    "invoice number",
                    "bill to",
                    "ship to",
                    "due date",
                    "payment terms",
                    "subtotal",
                    "tax",
                    "total amount",
                    "item description",
                    "quantity",
                    "unit price",
                ],
                "weight": 1.0,
            },
            DocumentType.RECEIPT: {
                "keywords": [
                    "receipt",
                    "transaction",
                    "payment method",
                    "card number",
                    "merchant",
                    "date/time",
                    "items purchased",
                    "total paid",
                    "thank you",
                ],
                "weight": 1.0,
            },
        }

    def classify(
        self, text: str, filename: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Classify document based on content.
        
        Args:
            text: Document text content
            filename: Optional filename for additional hints
            
        Returns:
            Dictionary with document_type and confidence score
        """
        logger.info("Classifying document", filename=filename)
        
        # Normalize text for matching
        text_lower = text.lower()
        
        # Calculate scores for each document type
        scores = {}
        for doc_type, patterns in self.classification_patterns.items():
            score = self._calculate_score(text_lower, patterns["keywords"])
            scores[doc_type] = score
        
        # Boost scores based on filename hints
        if filename:
            filename_lower = filename.lower()
            for doc_type in scores:
                if doc_type.value in filename_lower:
                    scores[doc_type] *= 1.5
        
        # Find best match
        if not scores or max(scores.values()) == 0:
            logger.warning("Could not classify document with confidence")
            return {
                "document_type": None,
                "confidence": 0.0,
                "scores": scores,
            }
        
        best_type = max(scores, key=scores.get)
        max_score = scores[best_type]
        
        # Normalize confidence (0-1 range)
        total_keywords = len(self.classification_patterns[best_type]["keywords"])
        confidence = min(max_score / total_keywords, 1.0)
        
        logger.info(
            "Document classified",
            document_type=best_type.value,
            confidence=confidence,
        )
        
        return {
            "document_type": best_type,
            "confidence": confidence,
            "scores": {k.value: v for k, v in scores.items()},
        }

    def _calculate_score(self, text: str, keywords: list[str]) -> float:
        """Calculate matching score based on keyword presence."""
        score = 0.0
        
        for keyword in keywords:
            # Exact phrase match
            if keyword in text:
                score += 1.0
                
                # Bonus for multiple occurrences
                occurrences = text.count(keyword)
                if occurrences > 1:
                    score += 0.1 * min(occurrences - 1, 3)  # Cap bonus at 3 extra
        
        return score

    def classify_with_llm(self, text: str, filename: Optional[str] = None) -> Dict[str, any]:
        """
        Classify document using LLM for more accurate results.
        
        This method uses GPT to classify documents when rule-based
        classification has low confidence.
        """
        from langchain_openai import ChatOpenAI
        
        logger.info("Classifying document with LLM")
        
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.0,
            api_key=settings.OPENAI_API_KEY,
        )
        
        # Truncate text if too long
        max_chars = 4000
        text_sample = text[:max_chars] if len(text) > max_chars else text
        
        prompt = f"""Classify the following document into one of these categories:
- policy: Insurance policy document
- claim: Insurance claim form
- eob: Explanation of Benefits
- invoice: Invoice or bill
- receipt: Payment receipt

Document text:
{text_sample}

Respond with JSON in this format:
{{"document_type": "type", "confidence": 0.95, "reasoning": "brief explanation"}}

Response:"""
        
        try:
            response = llm.invoke(prompt)
            
            # Parse response
            import json
            result = json.loads(response.content)
            
            # Convert string to enum
            doc_type_str = result.get("document_type")
            if doc_type_str:
                result["document_type"] = DocumentType(doc_type_str)
            
            logger.info(
                "LLM classification complete",
                document_type=result.get("document_type"),
                confidence=result.get("confidence"),
            )
            
            return result
            
        except Exception as e:
            logger.error("LLM classification failed", error=str(e), exc_info=True)
            # Fall back to rule-based
            return self.classify(text, filename)


# Global classifier instance
document_classifier = DocumentClassifier()


def get_document_classifier() -> DocumentClassifier:
    """Get document classifier instance."""
    return document_classifier
