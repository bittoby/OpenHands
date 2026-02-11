"""Store for managing verified LLM models in the database."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import and_, or_
from sqlalchemy.orm import sessionmaker
from storage.database import session_maker
from storage.verified_model import VerifiedModel

from openhands.core.logger import openhands_logger as logger


@dataclass
class VerifiedModelStore:
    """Store for CRUD operations on verified models."""

    session_maker: sessionmaker

    def get_all_models(self) -> list[VerifiedModel]:
        """Get all verified models from the database.

        Note: Returns detached SQLAlchemy instances. Once the session closes,
        the instances are detached from the session. This is intentional for
        read-only operations, but callers should not attempt to modify and
        save these instances.

        Returns:
            list[VerifiedModel]: All models in the database (detached instances)
        """
        with self.session_maker() as session:
            models = session.query(VerifiedModel).all()
            # Explicitly detach all instances to make behavior clear
            session.expunge_all()
            return models

    def get_enabled_models(self) -> list[VerifiedModel]:
        """Get all enabled verified models.

        Returns:
            list[VerifiedModel]: All enabled models
        """
        with self.session_maker() as session:
            models = (
                session.query(VerifiedModel)
                .filter(VerifiedModel.is_enabled == True)  # noqa: E712
                .all()
            )
            return models

    def get_verified_models(self) -> list[VerifiedModel]:
        """Get all verified and enabled models.

        Returns:
            list[VerifiedModel]: All verified and enabled models
        """
        with self.session_maker() as session:
            models = (
                session.query(VerifiedModel)
                .filter(
                    and_(
                        VerifiedModel.is_verified == True,  # noqa: E712
                        VerifiedModel.is_enabled == True,  # noqa: E712
                    )
                )
                .all()
            )
            return models

    def get_models_by_provider(self, provider: str) -> list[VerifiedModel]:
        """Get all enabled models for a specific provider.

        Args:
            provider: The provider name (e.g., 'openhands', 'anthropic')

        Returns:
            list[VerifiedModel]: All enabled models for the provider
        """
        with self.session_maker() as session:
            models = (
                session.query(VerifiedModel)
                .filter(
                    and_(
                        VerifiedModel.provider == provider,
                        VerifiedModel.is_enabled == True,  # noqa: E712
                    )
                )
                .all()
            )
            return models

    def get_model_by_name(self, model_name: str) -> VerifiedModel | None:
        """Get a model by its name.

        Args:
            model_name: The model name to look up

        Returns:
            VerifiedModel | None: The model if found, None otherwise
        """
        with self.session_maker() as session:
            model = (
                session.query(VerifiedModel)
                .filter(VerifiedModel.model_name == model_name)
                .first()
            )
            return model

    def create_model(
        self,
        model_name: str,
        provider: str,
        is_verified: bool = True,
        is_enabled: bool = True,
        supports_function_calling: bool = False,
        supports_vision: bool = False,
        supports_prompt_cache: bool = False,
        supports_reasoning_effort: bool = False,
    ) -> VerifiedModel:
        """Create a new verified model.

        Args:
            model_name: The model identifier
            provider: The provider name
            is_verified: Whether the model is verified
            is_enabled: Whether the model is enabled
            supports_function_calling: Whether the model supports function calling
            supports_vision: Whether the model supports vision
            supports_prompt_cache: Whether the model supports prompt caching
            supports_reasoning_effort: Whether the model supports reasoning effort

        Returns:
            VerifiedModel: The created model

        Raises:
            ValueError: If a model with the same name already exists
        """
        with self.session_maker() as session:
            # Check if model already exists
            existing = (
                session.query(VerifiedModel)
                .filter(VerifiedModel.model_name == model_name)
                .first()
            )
            if existing:
                raise ValueError(f'Model {model_name} already exists')

            model = VerifiedModel(
                model_name=model_name,
                provider=provider,
                is_verified=is_verified,
                is_enabled=is_enabled,
                supports_function_calling=supports_function_calling,
                supports_vision=supports_vision,
                supports_prompt_cache=supports_prompt_cache,
                supports_reasoning_effort=supports_reasoning_effort,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            logger.info(f'Created verified model: {model_name}')
            return model

    def update_model(
        self,
        model_name: str,
        is_verified: bool | None = None,
        is_enabled: bool | None = None,
        supports_function_calling: bool | None = None,
        supports_vision: bool | None = None,
        supports_prompt_cache: bool | None = None,
        supports_reasoning_effort: bool | None = None,
    ) -> VerifiedModel | None:
        """Update an existing verified model.

        Args:
            model_name: The model name to update
            is_verified: Whether the model is verified (optional)
            is_enabled: Whether the model is enabled (optional)
            supports_function_calling: Whether the model supports function calling (optional)
            supports_vision: Whether the model supports vision (optional)
            supports_prompt_cache: Whether the model supports prompt caching (optional)
            supports_reasoning_effort: Whether the model supports reasoning effort (optional)

        Returns:
            VerifiedModel | None: The updated model if found, None otherwise
        """
        with self.session_maker() as session:
            model = (
                session.query(VerifiedModel)
                .filter(VerifiedModel.model_name == model_name)
                .first()
            )
            if not model:
                return None

            if is_verified is not None:
                model.is_verified = is_verified
            if is_enabled is not None:
                model.is_enabled = is_enabled
            if supports_function_calling is not None:
                model.supports_function_calling = supports_function_calling
            if supports_vision is not None:
                model.supports_vision = supports_vision
            if supports_prompt_cache is not None:
                model.supports_prompt_cache = supports_prompt_cache
            if supports_reasoning_effort is not None:
                model.supports_reasoning_effort = supports_reasoning_effort

            session.commit()
            session.refresh(model)
            logger.info(f'Updated verified model: {model_name}')
            return model

    def delete_model(self, model_name: str) -> bool:
        """Delete a verified model.

        Args:
            model_name: The model name to delete

        Returns:
            bool: True if deleted, False if not found
        """
        with self.session_maker() as session:
            model = (
                session.query(VerifiedModel)
                .filter(VerifiedModel.model_name == model_name)
                .first()
            )
            if not model:
                return False

            session.delete(model)
            session.commit()
            logger.info(f'Deleted verified model: {model_name}')
            return True

    def bulk_create_models(self, models: list[dict]) -> int:
        """Bulk create multiple models.

        Note: This operation is all-or-nothing. If any model fails to create
        (e.g., constraint violation, validation error), the entire transaction
        rolls back and returns 0. All models must be valid for any to be created.

        Args:
            models: List of model dictionaries with keys matching VerifiedModel fields

        Returns:
            int: Number of models created (0 if any model fails)
        """
        with self.session_maker() as session:
            created_count = 0
            try:
                for model_data in models:
                    # Check if model already exists
                    existing = (
                        session.query(VerifiedModel)
                        .filter(VerifiedModel.model_name == model_data['model_name'])
                        .first()
                    )
                    if existing:
                        logger.debug(
                            f'Model {model_data["model_name"]} already exists, skipping'
                        )
                        continue

                    model = VerifiedModel(**model_data)
                    session.add(model)
                    created_count += 1

                session.commit()
                logger.info(f'Bulk created {created_count} verified models')
                return created_count
            except Exception as e:
                session.rollback()
                logger.error(f'Error during bulk create: {e}')
                raise

    @classmethod
    def get_instance(cls) -> VerifiedModelStore:
        """Get an instance of the VerifiedModelStore.

        Returns:
            VerifiedModelStore: A new instance using the default session maker
        """
        return VerifiedModelStore(session_maker)
