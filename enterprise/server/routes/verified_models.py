"""API routes for managing verified LLM models."""

import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from server.email_validation import get_admin_user_id
from storage.verified_model_store import VerifiedModelStore

from openhands.core.logger import openhands_logger as logger

# Initialize API router and store
api_router = APIRouter(prefix='/api/admin/verified-models')
verified_model_store = VerifiedModelStore.get_instance()


class VerifiedModelCreate(BaseModel):
    """Request model for creating a verified model."""

    model_name: str
    provider: str
    is_verified: bool = True
    is_enabled: bool = True
    supports_function_calling: bool = False
    supports_vision: bool = False
    supports_prompt_cache: bool = False
    supports_reasoning_effort: bool = False


class VerifiedModelUpdate(BaseModel):
    """Request model for updating a verified model."""

    is_verified: bool | None = None
    is_enabled: bool | None = None
    supports_function_calling: bool | None = None
    supports_vision: bool | None = None
    supports_prompt_cache: bool | None = None
    supports_reasoning_effort: bool | None = None


class VerifiedModelResponse(BaseModel):
    """Response model for a verified model."""

    id: int
    model_name: str
    provider: str
    is_verified: bool
    is_enabled: bool
    supports_function_calling: bool
    supports_vision: bool
    supports_prompt_cache: bool
    supports_reasoning_effort: bool
    created_at: str
    updated_at: str


class BulkCreateRequest(BaseModel):
    """Request model for bulk creating models."""

    models: list[VerifiedModelCreate]


class BulkCreateResponse(BaseModel):
    """Response model for bulk create operation."""

    created_count: int
    message: str


def _model_to_response(model) -> dict:
    """Convert a VerifiedModel to response dict.

    Args:
        model: The VerifiedModel instance

    Returns:
        dict: Response dictionary matching VerifiedModelResponse schema
    """
    return {
        'id': model.id,
        'model_name': model.model_name,
        'provider': model.provider,
        'is_verified': model.is_verified,
        'is_enabled': model.is_enabled,
        'supports_function_calling': model.supports_function_calling,
        'supports_vision': model.supports_vision,
        'supports_prompt_cache': model.supports_prompt_cache,
        'supports_reasoning_effort': model.supports_reasoning_effort,
        'created_at': model.created_at.isoformat() if model.created_at else '',
        'updated_at': model.updated_at.isoformat() if model.updated_at else '',
    }


def _validate_model_input(model_name: str, provider: str) -> None:
    """Validate model_name and provider inputs.

    Args:
        model_name: The model name to validate
        provider: The provider name to validate

    Raises:
        HTTPException: If validation fails
    """
    # Validate model_name - must start and end with alphanumeric, special chars only in middle
    if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9_.-]*[a-zA-Z0-9])?$', model_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='model_name must start and end with alphanumeric characters, with hyphens, underscores, and dots allowed in the middle',
        )
    if len(model_name) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='model_name exceeds maximum length of 255 characters',
        )

    # Validate provider - must start and end with alphanumeric
    if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9_-]*[a-zA-Z0-9])?$', provider):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='provider must start and end with alphanumeric characters, with hyphens and underscores allowed in the middle',
        )
    if len(provider) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='provider exceeds maximum length of 100 characters',
        )


@api_router.get('', response_model=list[VerifiedModelResponse])
async def list_verified_models(
    provider: str | None = None,
    enabled_only: bool = False,
    verified_only: bool = False,
    limit: int = 100,
    offset: int = 0,
    user_id: str = Depends(get_admin_user_id),
):
    """List all verified models.

    Args:
        provider: Optional provider filter
        enabled_only: If True, only return enabled models
        verified_only: If True, only return verified models
        limit: Maximum number of models to return (default: 100, max: 1000)
        offset: Number of models to skip (default: 0)
        user_id: Authenticated admin user ID (from dependency)

    Returns:
        list[VerifiedModelResponse]: List of verified models
    """
    # Validate pagination parameters
    if limit < 1 or limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='limit must be between 1 and 1000',
        )
    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='offset must be non-negative',
        )

    try:
        if provider:
            models = verified_model_store.get_models_by_provider(provider)
        elif verified_only:
            models = verified_model_store.get_verified_models()
        elif enabled_only:
            models = verified_model_store.get_enabled_models()
        else:
            models = verified_model_store.get_all_models()

        # Apply pagination
        paginated_models = models[offset : offset + limit]

        return [_model_to_response(model) for model in paginated_models]
    except Exception:
        logger.exception('Error listing verified models')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to list verified models',
        )


@api_router.get('/{model_name}', response_model=VerifiedModelResponse)
async def get_verified_model(
    model_name: str, user_id: str = Depends(get_admin_user_id)
):
    """Get a specific verified model by name.

    Args:
        model_name: The model name to retrieve
        user_id: Authenticated admin user ID (from dependency)

    Returns:
        VerifiedModelResponse: The verified model
    """
    try:
        model = verified_model_store.get_model_by_name(model_name)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Model {model_name} not found',
            )

        return _model_to_response(model)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f'Error getting verified model: {model_name}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to get verified model',
        )


@api_router.post('', response_model=VerifiedModelResponse, status_code=201)
async def create_verified_model(
    model_data: VerifiedModelCreate, user_id: str = Depends(get_admin_user_id)
):
    """Create a new verified model.

    Args:
        model_data: The model data to create
        user_id: Authenticated admin user ID (from dependency)

    Returns:
        VerifiedModelResponse: The created model
    """
    try:
        # Validate inputs
        _validate_model_input(model_data.model_name, model_data.provider)

        model = verified_model_store.create_model(
            model_name=model_data.model_name,
            provider=model_data.provider,
            is_verified=model_data.is_verified,
            is_enabled=model_data.is_enabled,
            supports_function_calling=model_data.supports_function_calling,
            supports_vision=model_data.supports_vision,
            supports_prompt_cache=model_data.supports_prompt_cache,
            supports_reasoning_effort=model_data.supports_reasoning_effort,
        )

        return _model_to_response(model)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception('Error creating verified model')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to create verified model',
        )


@api_router.put('/{model_name}', response_model=VerifiedModelResponse)
async def update_verified_model(
    model_name: str,
    model_data: VerifiedModelUpdate,
    user_id: str = Depends(get_admin_user_id),
):
    """Update an existing verified model.

    Args:
        model_name: The model name to update
        model_data: The fields to update
        user_id: Authenticated admin user ID (from dependency)

    Returns:
        VerifiedModelResponse: The updated model
    """
    try:
        model = verified_model_store.update_model(
            model_name=model_name,
            is_verified=model_data.is_verified,
            is_enabled=model_data.is_enabled,
            supports_function_calling=model_data.supports_function_calling,
            supports_vision=model_data.supports_vision,
            supports_prompt_cache=model_data.supports_prompt_cache,
            supports_reasoning_effort=model_data.supports_reasoning_effort,
        )

        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Model {model_name} not found',
            )

        return _model_to_response(model)
    except HTTPException:
        raise
    except Exception:
        logger.exception(f'Error updating verified model: {model_name}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to update verified model',
        )


@api_router.delete('/{model_name}')
async def delete_verified_model(
    model_name: str, user_id: str = Depends(get_admin_user_id)
):
    """Delete a verified model.

    Args:
        model_name: The model name to delete
        user_id: Authenticated admin user ID (from dependency)

    Returns:
        dict: Success message
    """
    try:
        success = verified_model_store.delete_model(model_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Model {model_name} not found',
            )

        return {'message': f'Model {model_name} deleted successfully'}
    except HTTPException:
        raise
    except Exception:
        logger.exception(f'Error deleting verified model: {model_name}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to delete verified model',
        )


@api_router.post('/bulk', response_model=BulkCreateResponse)
async def bulk_create_verified_models(
    request: BulkCreateRequest, user_id: str = Depends(get_admin_user_id)
):
    """Bulk create multiple verified models.

    Args:
        request: The bulk create request with list of models
        user_id: Authenticated admin user ID (from dependency)

    Returns:
        BulkCreateResponse: Number of models created
    """
    try:
        # Validate all models before creating
        for model in request.models:
            _validate_model_input(model.model_name, model.provider)

        models_data = [model.model_dump() for model in request.models]
        created_count = verified_model_store.bulk_create_models(models_data)

        return {
            'created_count': created_count,
            'message': f'Successfully created {created_count} models',
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception('Error bulk creating verified models')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to bulk create verified models',
        )
