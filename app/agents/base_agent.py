"""
Base Agent Class for Mobius Multi-Agent System

This module defines the abstract base class for all specialized agents
in the Mobius platform. Each agent represents a specific capability
within the context engineering system.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.core.logging import logger


class AgentStatus(str, Enum):
    """Enumeration of possible agent statuses."""

    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(str, Enum):
    """Enumeration of agent types in the system."""

    ORCHESTRATOR = "orchestrator"
    CONTEXT_BUILDER = "context_builder"
    RETRIEVAL = "retrieval"
    CODE_GENERATOR = "code_generator"
    ANALYZER = "analyzer"
    VALIDATOR = "validator"


class AgentMessage(BaseModel):
    """
    Message structure for inter-agent communication.

    Attributes:
        id: Unique message identifier
        sender: Agent ID of the sender
        recipient: Agent ID of the recipient
        message_type: Type of message (request, response, notification)
        payload: Message content
        timestamp: Message creation timestamp
    """

    id: UUID = Field(default_factory=uuid4)
    sender: UUID
    recipient: Optional[UUID] = None
    message_type: str
    payload: Dict[str, Any]
    timestamp: str
    correlation_id: Optional[UUID] = None


class AgentCapability(BaseModel):
    """
    Defines a specific capability of an agent.

    Attributes:
        name: Capability name
        description: Human-readable description
        input_schema: Expected input format
        output_schema: Expected output format
    """

    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the Mobius system.

    This class provides common functionality and defines the interface
    that all specialized agents must implement.
    """

    def __init__(
        self,
        agent_id: Optional[UUID] = None,
        name: Optional[str] = None,
        agent_type: AgentType = AgentType.CONTEXT_BUILDER,
    ):
        """
        Initialize the base agent.

        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name for the agent
            agent_type: Type of agent
        """
        self.id = agent_id or uuid4()
        self.name = name or f"{agent_type.value}_{self.id}"
        self.type = agent_type
        self.status = AgentStatus.IDLE
        self.capabilities: List[AgentCapability] = []
        self._message_queue: List[AgentMessage] = []

        logger.info(f"Initialized {self.type.value} agent: {self.name}")

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data according to the agent's specialized function.

        Args:
            input_data: Input data to process

        Returns:
            Dict[str, Any]: Processing results
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> List[AgentCapability]:
        """
        Get the list of capabilities this agent provides.

        Returns:
            List[AgentCapability]: Agent capabilities
        """
        pass

    async def receive_message(self, message: AgentMessage) -> None:
        """
        Receive a message from another agent.

        Args:
            message: The message to receive
        """
        self._message_queue.append(message)
        logger.debug(f"Agent {self.name} received message from {message.sender}")

    async def send_message(
        self,
        recipient: UUID,
        message_type: str,
        payload: Dict[str, Any],
        correlation_id: Optional[UUID] = None,
    ) -> AgentMessage:
        """
        Send a message to another agent.

        Args:
            recipient: ID of the recipient agent
            message_type: Type of message
            payload: Message content
            correlation_id: Optional correlation ID for message tracking

        Returns:
            AgentMessage: The sent message
        """
        message = AgentMessage(
            sender=self.id,
            recipient=recipient,
            message_type=message_type,
            payload=payload,
            timestamp=str(datetime.utcnow()),
            correlation_id=correlation_id,
        )

        # TODO: Implement actual message sending through the orchestrator
        logger.debug(f"Agent {self.name} sending message to {recipient}")

        return message

    def set_status(self, status: AgentStatus) -> None:
        """
        Update the agent's status.

        Args:
            status: New status
        """
        self.status = status
        logger.info(f"Agent {self.name} status changed to {status.value}")

    async def initialize(self) -> None:
        """
        Initialize agent resources and connections.

        Override this method in subclasses to perform agent-specific
        initialization tasks.
        """
        logger.info(f"Initializing agent {self.name}")
        self.capabilities = self.get_capabilities()

    async def shutdown(self) -> None:
        """
        Clean up agent resources.

        Override this method in subclasses to perform agent-specific
        cleanup tasks.
        """
        logger.info(f"Shutting down agent {self.name}")
        self.set_status(AgentStatus.IDLE)

    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(id={self.id}, name={self.name}, status={self.status.value})"
