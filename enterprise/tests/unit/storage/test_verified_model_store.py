"""Unit tests for VerifiedModelStore."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from storage.base import Base
from storage.verified_model_store import VerifiedModelStore


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    yield SessionLocal
    Base.metadata.drop_all(engine)


@pytest.fixture
def store(db_session):
    """Create a VerifiedModelStore instance for testing."""
    return VerifiedModelStore(session_maker=db_session)


def test_create_model(store):
    """Test creating a new verified model."""
    model = store.create_model(
        model_name='test-model',
        provider='test-provider',
        is_verified=True,
        is_enabled=True,
        supports_function_calling=True,
    )

    assert model.model_name == 'test-model'
    assert model.provider == 'test-provider'
    assert model.is_verified is True
    assert model.is_enabled is True
    assert model.supports_function_calling is True
    assert model.id is not None


def test_create_duplicate_model(store):
    """Test that creating a duplicate model raises ValueError."""
    store.create_model(model_name='test-model', provider='test-provider')

    with pytest.raises(ValueError, match='Model test-model already exists'):
        store.create_model(model_name='test-model', provider='test-provider')


def test_get_model_by_name(store):
    """Test retrieving a model by name."""
    store.create_model(model_name='test-model', provider='test-provider')

    model = store.get_model_by_name('test-model')
    assert model is not None
    assert model.model_name == 'test-model'

    # Test non-existent model
    assert store.get_model_by_name('non-existent') is None


def test_get_all_models(store):
    """Test retrieving all models."""
    store.create_model(model_name='model-1', provider='provider-1')
    store.create_model(model_name='model-2', provider='provider-2')

    models = store.get_all_models()
    assert len(models) == 2
    assert {m.model_name for m in models} == {'model-1', 'model-2'}


def test_get_enabled_models(store):
    """Test retrieving only enabled models."""
    store.create_model(model_name='enabled-model', provider='test', is_enabled=True)
    store.create_model(model_name='disabled-model', provider='test', is_enabled=False)

    models = store.get_enabled_models()
    assert len(models) == 1
    assert models[0].model_name == 'enabled-model'


def test_get_verified_models(store):
    """Test retrieving only verified and enabled models."""
    store.create_model(
        model_name='verified-enabled',
        provider='test',
        is_verified=True,
        is_enabled=True,
    )
    store.create_model(
        model_name='verified-disabled',
        provider='test',
        is_verified=True,
        is_enabled=False,
    )
    store.create_model(
        model_name='unverified-enabled',
        provider='test',
        is_verified=False,
        is_enabled=True,
    )

    models = store.get_verified_models()
    assert len(models) == 1
    assert models[0].model_name == 'verified-enabled'


def test_get_models_by_provider(store):
    """Test retrieving models by provider."""
    store.create_model(model_name='model-1', provider='provider-a')
    store.create_model(model_name='model-2', provider='provider-a')
    store.create_model(model_name='model-3', provider='provider-b')

    models = store.get_models_by_provider('provider-a')
    assert len(models) == 2
    assert {m.model_name for m in models} == {'model-1', 'model-2'}


def test_update_model(store):
    """Test updating a model."""
    store.create_model(
        model_name='test-model',
        provider='test',
        is_enabled=True,
        supports_function_calling=False,
    )

    updated = store.update_model(
        model_name='test-model', is_enabled=False, supports_function_calling=True
    )

    assert updated is not None
    assert updated.is_enabled is False
    assert updated.supports_function_calling is True

    # Test updating non-existent model
    assert store.update_model(model_name='non-existent', is_enabled=False) is None


def test_update_model_partial(store):
    """Test partial update of a model."""
    store.create_model(
        model_name='test-model',
        provider='test',
        is_enabled=True,
        is_verified=True,
        supports_function_calling=False,
    )

    # Update only one field
    updated = store.update_model(model_name='test-model', is_enabled=False)

    assert updated is not None
    assert updated.is_enabled is False
    assert updated.is_verified is True  # Should remain unchanged
    assert updated.supports_function_calling is False  # Should remain unchanged


def test_delete_model(store):
    """Test deleting a model."""
    store.create_model(model_name='test-model', provider='test')

    # Delete existing model
    assert store.delete_model('test-model') is True
    assert store.get_model_by_name('test-model') is None

    # Delete non-existent model
    assert store.delete_model('non-existent') is False


def test_bulk_create_models(store):
    """Test bulk creating multiple models."""
    models_data = [
        {
            'model_name': 'model-1',
            'provider': 'provider-1',
            'supports_function_calling': True,
        },
        {
            'model_name': 'model-2',
            'provider': 'provider-2',
            'supports_vision': True,
        },
        {'model_name': 'model-3', 'provider': 'provider-3'},
    ]

    created_count = store.bulk_create_models(models_data)
    assert created_count == 3

    all_models = store.get_all_models()
    assert len(all_models) == 3


def test_bulk_create_with_duplicates(store):
    """Test bulk create skips duplicates."""
    store.create_model(model_name='existing-model', provider='test')

    models_data = [
        {'model_name': 'existing-model', 'provider': 'test'},  # Duplicate
        {'model_name': 'new-model', 'provider': 'test'},
    ]

    created_count = store.bulk_create_models(models_data)
    assert created_count == 1  # Only new-model should be created

    all_models = store.get_all_models()
    assert len(all_models) == 2


def test_model_feature_flags(store):
    """Test all feature flags are stored correctly."""
    model = store.create_model(
        model_name='feature-test',
        provider='test',
        supports_function_calling=True,
        supports_vision=True,
        supports_prompt_cache=True,
        supports_reasoning_effort=True,
    )

    assert model.supports_function_calling is True
    assert model.supports_vision is True
    assert model.supports_prompt_cache is True
    assert model.supports_reasoning_effort is True

    # Verify retrieval
    retrieved = store.get_model_by_name('feature-test')
    assert retrieved.supports_function_calling is True
    assert retrieved.supports_vision is True
    assert retrieved.supports_prompt_cache is True
    assert retrieved.supports_reasoning_effort is True
