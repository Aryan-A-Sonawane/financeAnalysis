"""Base agent class for all LangGraph agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AgentState(BaseModel):
    """Base state for all agents."""
    
    # Input
    document_id: Optional[str] = None
    text: Optional[str] = None
    document_type: Optional[str] = None
    
    # Processing
    current_step: str = "initial"
    iterations: int = 0
    max_iterations: int = 10
    
    # Results
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)
    classifications: Dict[str, Any] = Field(default_factory=dict)
    analysis: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    
    # Metadata
    confidence: float = 0.0
    processing_time: float = 0.0
    
    class Config:
        arbitrary_types_allowed = True


class BaseAgent(ABC):
    """Base class for all LangGraph agents."""

    def __init__(self, name: str, description: str):
        """Initialize agent."""
        self.name = name
        self.description = description
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        self.logger = get_logger(f"agent.{name}")

    @abstractmethod
    def create_prompt(self) -> ChatPromptTemplate:
        """Create the prompt template for this agent."""
        pass

    @abstractmethod
    async def process(self, state: AgentState) -> AgentState:
        """Process the current state and return updated state."""
        pass

    def should_continue(self, state: AgentState) -> bool:
        """Determine if agent should continue processing."""
        return (
            state.iterations < state.max_iterations
            and len(state.errors) == 0
        )

    async def run(self, state: AgentState) -> AgentState:
        """Run the agent with the given state."""
        self.logger.info(
            "Agent starting",
            agent=self.name,
            step=state.current_step,
        )
        
        try:
            result = await self.process(state)
            self.logger.info(
                "Agent completed",
                agent=self.name,
                confidence=result.confidence,
            )
            return result
        except Exception as e:
            self.logger.error(
                "Agent failed",
                agent=self.name,
                error=str(e),
                exc_info=True,
            )
            state.errors.append(f"{self.name}: {str(e)}")
            return state
