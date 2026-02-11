"""Create verified_models table.

Revision ID: 092
Revises: 091
Create Date: 2025-02-10 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "092"
down_revision: Union[str, None] = "091"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create verified_models table
    op.create_table(
        "verified_models",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column(
            "is_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "supports_function_calling",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "supports_vision",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "supports_prompt_cache",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "supports_reasoning_effort",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("model_name"),
    )
    op.create_index(
        op.f("ix_verified_models_model_name"),
        "verified_models",
        ["model_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_verified_models_provider"),
        "verified_models",
        ["provider"],
        unique=False,
    )

    # Seed initial data from hardcoded arrays
    # OpenHands provider models
    openhands_models = [
        {
            "model_name": "claude-sonnet-4-20250514",
            "provider": "openhands",
            "supports_function_calling": True,
        },
        {
            "model_name": "claude-sonnet-4-5-20250929",
            "provider": "openhands",
            "supports_function_calling": True,
        },
        {
            "model_name": "claude-haiku-4-5-20251001",
            "provider": "openhands",
            "supports_function_calling": True,
        },
        {
            "model_name": "claude-opus-4-20250514",
            "provider": "openhands",
            "supports_function_calling": True,
        },
        {
            "model_name": "claude-opus-4-1-20250805",
            "provider": "openhands",
            "supports_function_calling": True,
        },
        {
            "model_name": "claude-opus-4-5-20251101",
            "provider": "openhands",
            "supports_function_calling": True,
        },
        {
            "model_name": "gpt-5.2",
            "provider": "openhands",
            "supports_function_calling": True,
        },
        {
            "model_name": "gpt-5.2-codex",
            "provider": "openhands",
            "supports_function_calling": True,
        },
        {
            "model_name": "gemini-2.5-pro",
            "provider": "openhands",
            "supports_function_calling": True,
            "supports_reasoning_effort": True,
        },
        {
            "model_name": "o3",
            "provider": "openhands",
            "supports_reasoning_effort": True,
        },
        {
            "model_name": "o3-mini-2025-01-31",
            "provider": "openhands",
            "supports_reasoning_effort": True,
        },
        {
            "model_name": "o3-2025-04-16",
            "provider": "openhands",
            "supports_reasoning_effort": True,
        },
        {
            "model_name": "o4-mini",
            "provider": "openhands",
            "supports_reasoning_effort": True,
        },
        {
            "model_name": "o4-mini-2025-04-16",
            "provider": "openhands",
            "supports_reasoning_effort": True,
        },
        {
            "model_name": "devstral-small-2505",
            "provider": "openhands",
            "supports_function_calling": True,
        },
        {
            "model_name": "devstral-small-2507",
            "provider": "openhands",
            "supports_function_calling": True,
        },
        {
            "model_name": "devstral-medium-2507",
            "provider": "openhands",
            "supports_function_calling": True,
        },
        {
            "model_name": "kimi-k2-0711-preview",
            "provider": "openhands",
            "supports_function_calling": True,
        },
        {
            "model_name": "qwen3-coder-480b",
            "provider": "openhands",
            "supports_function_calling": True,
        },
    ]

    # Anthropic models
    anthropic_models = [
        {
            "model_name": "claude-3-5-sonnet-20241022",
            "provider": "anthropic",
            "supports_function_calling": True,
            "supports_vision": True,
            "supports_prompt_cache": True,
        },
        {
            "model_name": "claude-3-7-sonnet-20250219",
            "provider": "anthropic",
            "supports_function_calling": True,
            "supports_vision": True,
            "supports_prompt_cache": True,
        },
    ]

    # OpenAI models
    openai_models = [
        {
            "model_name": "deepseek-chat",
            "provider": "openai",
            "supports_function_calling": True,
        },
    ]

    # Insert all models
    all_models = openhands_models + anthropic_models + openai_models
    for model in all_models:
        op.execute(
            sa.text(
                """
            INSERT INTO verified_models (
                model_name, provider, is_verified, is_enabled,
                supports_function_calling, supports_vision,
                supports_prompt_cache, supports_reasoning_effort
            ) VALUES (
                :model_name, :provider, true, true,
                :supports_function_calling, :supports_vision,
                :supports_prompt_cache, :supports_reasoning_effort
            )
        """
            ).bindparams(
                model_name=model["model_name"],
                provider=model["provider"],
                supports_function_calling=model.get("supports_function_calling", False),
                supports_vision=model.get("supports_vision", False),
                supports_prompt_cache=model.get("supports_prompt_cache", False),
                supports_reasoning_effort=model.get("supports_reasoning_effort", False),
            )
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_verified_models_provider"), table_name="verified_models")
    op.drop_index(op.f("ix_verified_models_model_name"), table_name="verified_models")
    op.drop_table("verified_models")
