"""SQLAlchemy model for verified LLM models.

This model stores the list of verified models that are available
in the OpenHands Cloud model selector, allowing dynamic updates
without requiring code deployments.
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, text
from storage.base import Base


class VerifiedModel(Base):
    """Represents a verified LLM model available in OpenHands Cloud.

    Attributes:
        id: Primary key
        model_name: The model identifier (e.g., 'claude-opus-4-5-20251101')
        provider: The provider name (e.g., 'openhands', 'anthropic', 'openai')
        is_verified: Whether this model is shown in the verified section
        is_enabled: Whether this model is currently available
        supports_function_calling: Whether the model supports function calling
        supports_vision: Whether the model supports vision/image inputs
        supports_prompt_cache: Whether the model supports prompt caching
        supports_reasoning_effort: Whether the model supports reasoning effort parameters
        created_at: Timestamp when the model was added
        updated_at: Timestamp when the model was last updated
    """

    __tablename__ = "verified_models"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(255), nullable=False, unique=True, index=True)
    provider = Column(String(100), nullable=False, index=True)
    is_verified = Column(Boolean, nullable=False, default=True, server_default="true")
    is_enabled = Column(Boolean, nullable=False, default=True, server_default="true")
    supports_function_calling = Column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    supports_vision = Column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    supports_prompt_cache = Column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    supports_reasoning_effort = Column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    created_at = Column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
    updated_at = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
