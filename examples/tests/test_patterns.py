"""
PATTERN: Testing Patterns for Async FastAPI Application
USE WHEN: Writing unit and integration tests for the BRD/PRD generator
KEY CONCEPTS:
- Async test functions with pytest-asyncio
- Mocking dependencies for isolation
- Testing with FastAPI TestClient
- Fixture-based test data management
"""
# Source: https://fastapi.tiangolo.com/tutorial/testing/

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from typing import AsyncGenerator

from ..api.dependencies import (
    app,
    get_document_service,
    DocumentGenerationRequest,
    DocumentGenerationService
)
from ..api.llm_strategy_base import Document
from ..api.llm_strategies import OpenAIStrategy

# --- Fixtures ---
@pytest.fixture
def test_client():
    """Provides a FastAPI test client."""
    return TestClient(app)

@pytest.fixture
async def mock_llm_strategy():
    """Provides a mock LLM strategy for testing."""
    mock = AsyncMock(spec=OpenAIStrategy)
    mock.generate.return_value = Document(
        content="Mock generated document",
        provider="mock",
        cost=0.01,
        tokens_used=100,
        generation_time_ms=50.0
    )
    mock.get_capabilities.return_value = MagicMock(
        max_context_tokens=10000,
        supports_json_mode=True,
        supports_function_calling=True,
        cost_per_1k_tokens=0.01
    )
    return mock

@pytest.fixture
def mock_document_service(mock_llm_strategy):
    """Provides a mock document generation service."""
    mock_factory = MagicMock()
    mock_factory.get_optimal_strategy.return_value = mock_llm_strategy

    service = DocumentGenerationService(mock_factory, None)
    return service

# --- Unit Tests ---
@pytest.mark.asyncio
async def test_llm_strategy_generate(mock_llm_strategy):
    """Test that the LLM strategy generates documents correctly."""
    result = await mock_llm_strategy.generate("test prompt", "test idea")

    assert result.content == "Mock generated document"
    assert result.provider == "mock"
    assert result.cost == 0.01
    assert result.tokens_used == 100
    mock_llm_strategy.generate.assert_called_once_with("test prompt", "test idea")

@pytest.mark.asyncio
async def test_document_service_generate(mock_document_service):
    """Test the document generation service orchestration."""
    request = DocumentGenerationRequest(
        user_idea="Create a mobile app for dog walkers",
        document_type="brd",
        complexity="simple"
    )

    response = await mock_document_service.generate_document(request)

    assert response.content == "Mock generated document"
    assert response.cost == 0.01
    assert response.provider_used == "mock"

# --- Integration Tests ---
def test_generate_endpoint_success(test_client, mock_document_service):
    """Test the /generate endpoint with a successful request."""
    # Override the dependency with our mock
    app.dependency_overrides[get_document_service] = lambda: mock_document_service

    response = test_client.post(
        "/generate",
        json={
            "user_idea": "Create a task management system",
            "document_type": "prd",
            "complexity": "moderate"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data
    assert data["cost"] == 0.01

    # Clean up override
    app.dependency_overrides.clear()

def test_generate_endpoint_validation_error(test_client):
    """Test the /generate endpoint with invalid input."""
    response = test_client.post(
        "/generate",
        json={
            "user_idea": "",  # Empty idea should fail validation
            "document_type": "invalid_type"
        }
    )

    assert response.status_code == 422  # Validation error

# --- Repository Pattern Tests ---
@pytest.mark.asyncio
async def test_repository_save_and_retrieve():
    """Test the repository pattern with an in-memory database."""
    # This would use an in-memory SQLite database for testing
    # Implementation depends on your specific models
    pass

# --- Factory Pattern Tests ---
def test_factory_provider_selection():
    """Test that the factory selects the correct provider based on complexity."""
    from ..api.llm_factory import LLMFactory, TaskComplexity, ProviderName

    # Mock environment variables for API keys
    import os
    os.environ["OPENAI_API_KEY"] = "test_key"
    os.environ["CLAUDE_API_KEY"] = "test_key"
    os.environ["GEMINI_API_KEY"] = "test_key"

    # Test simple complexity -> Gemini
    strategy = LLMFactory.get_optimal_strategy(task_complexity=TaskComplexity.SIMPLE)
    assert strategy is not None  # Would check provider type in real test

    # Clean up
    for key in ["OPENAI_API_KEY", "CLAUDE_API_KEY", "GEMINI_API_KEY"]:
        os.environ.pop(key, None)

# --- Async Context Manager Tests ---
@pytest.mark.asyncio
async def test_database_session_lifecycle():
    """Test that database sessions are properly managed."""
    # This would test the get_db_session dependency
    # Ensuring proper commit/rollback/close behavior
    pass

# --- Performance Tests ---
@pytest.mark.asyncio
async def test_concurrent_document_generation():
    """Test that multiple document generations can run concurrently."""
    import asyncio
    from ..api.llm_strategies import GeminiStrategy

    # Create multiple mock strategies
    strategies = [AsyncMock(spec=GeminiStrategy) for _ in range(5)]
    for strategy in strategies:
        strategy.generate.return_value = Document(
            content="Concurrent test",
            provider="gemini",
            cost=0.02,
            tokens_used=50,
            generation_time_ms=100.0
        )

    # Run concurrent generations
    tasks = [strategy.generate("prompt", f"idea_{i}") for i, strategy in enumerate(strategies)]
    results = await asyncio.gather(*tasks)

    assert len(results) == 5
    assert all(r.content == "Concurrent test" for r in results)