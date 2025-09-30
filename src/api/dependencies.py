"""
Dependency injection for FastAPI application.
"""

from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from datetime import datetime, timedelta
import hashlib
import hmac

from ..core.generator import DocumentGenerator
from ..core.validator import DocumentValidator
from ..core.prompts import PromptBuilder
from ..llm import get_llm_factory, LLMFactory
from ..repository import get_repository, BaseRepository

# Security
security = HTTPBearer(auto_error=False)


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests = {}

    def check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit."""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)

        # Clean old entries
        self.requests = {
            k: v for k, v in self.requests.items()
            if v > minute_ago
        }

        # Count requests from this client
        client_requests = [
            t for k, t in self.requests.items()
            if k.startswith(client_id)
        ]

        if len(client_requests) >= self.requests_per_minute:
            return False

        # Record this request
        request_key = f"{client_id}:{now.timestamp()}"
        self.requests[request_key] = now
        return True


# Global instances
rate_limiter = RateLimiter(requests_per_minute=10)
_document_generator: Optional[DocumentGenerator] = None
_llm_factory: Optional[LLMFactory] = None
_repository: Optional[BaseRepository] = None


def get_llm_factory_instance() -> LLMFactory:
    """Get or create LLM factory singleton."""
    global _llm_factory
    if _llm_factory is None:
        _llm_factory = get_llm_factory()
    return _llm_factory


def get_repository_instance() -> BaseRepository:
    """Get or create repository singleton."""
    global _repository
    if _repository is None:
        _repository = get_repository(
            repository_type="filesystem",
            base_path=os.getenv("DOCUMENT_STORAGE_PATH", "./data/documents"),
            use_cache=True
        )
    return _repository


def get_document_generator() -> DocumentGenerator:
    """Get or create document generator singleton."""
    global _document_generator
    if _document_generator is None:
        _document_generator = DocumentGenerator(
            llm_factory=get_llm_factory_instance(),
            repository=get_repository_instance(),
            validator=DocumentValidator(),
            prompt_builder=PromptBuilder()
        )
    return _document_generator


async def verify_api_key(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)]
) -> str:
    """
    Verify API key from Authorization header.

    Args:
        credentials: Bearer token from header

    Returns:
        Client ID extracted from API key

    Raises:
        HTTPException: If API key is invalid
    """
    if not credentials:
        # In development, allow no auth
        if os.getenv("ENVIRONMENT", "development") == "development":
            return "dev_client"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    api_key = credentials.credentials

    # Validate API key format (simple validation for now)
    if not api_key or len(api_key) < 32:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract client ID from API key (first 8 chars for simplicity)
    client_id = api_key[:8]

    # In production, would verify against database
    # For now, just check against environment variable
    valid_keys = os.getenv("VALID_API_KEYS", "").split(",")
    if valid_keys and api_key not in valid_keys:
        if os.getenv("ENVIRONMENT") != "development":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return client_id


async def check_rate_limit(
    client_id: Annotated[str, Depends(verify_api_key)]
) -> str:
    """
    Check rate limit for client.

    Args:
        client_id: Client identifier from API key

    Returns:
        Client ID if within rate limit

    Raises:
        HTTPException: If rate limit exceeded
    """
    if not rate_limiter.check_rate_limit(client_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": "60"}
        )

    return client_id


# Dependency aliases for cleaner code
GeneratorDep = Annotated[DocumentGenerator, Depends(get_document_generator)]
RepositoryDep = Annotated[BaseRepository, Depends(get_repository_instance)]
ClientIdDep = Annotated[str, Depends(check_rate_limit)]
ValidatorDep = Annotated[DocumentValidator, Depends(lambda: DocumentValidator())]


class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections = {}

    async def connect(self, client_id: str, websocket):
        """Accept WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket

    async def disconnect(self, client_id: str):
        """Remove WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_message(self, client_id: str, message: dict):
        """Send message to specific client."""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_json(message)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        for websocket in self.active_connections.values():
            await websocket.send_json(message)


# Global WebSocket manager
ws_manager = WebSocketManager()