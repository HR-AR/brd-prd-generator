"""
PATTERN: Dependency Injection with FastAPI
USE WHEN: Managing shared resources and services across API endpoints
KEY CONCEPTS:
- Resource lifecycle management with yield
- Hierarchical dependencies
- Testability through dependency override
- Singleton-like patterns for expensive objects
"""
# Source: https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/

from typing import Annotated, AsyncGenerator, Optional
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel

from ..database.repository_concrete import SQLAlchemyRepository
from .llm_factory import LLMFactory, TaskComplexity

# --- Configuration (from environment in production) ---
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/brd_prd_db"

# --- Database Setup (Application Startup) ---
engine = None
AsyncSessionLocal = None

def init_db(db_url: str = DATABASE_URL):
    """Initialize database connection. Call at app startup."""
    global engine, AsyncSessionLocal
    engine = create_async_engine(db_url, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# --- Singleton Factory Instance (Application Startup) ---
llm_factory = LLMFactory()

# --- Pydantic Models for Request/Response ---
class DocumentGenerationRequest(BaseModel):
    user_idea: str
    document_type: Literal["brd", "prd", "both"]
    complexity: Optional[TaskComplexity] = TaskComplexity.MODERATE
    max_cost: Optional[float] = 2.0

class DocumentGenerationResponse(BaseModel):
    document_id: str
    content: str
    cost: float
    provider_used: str
    generation_time_ms: float

# --- Dependencies ---
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session per request.
    Properly manages transaction lifecycle with yield.
    """
    if AsyncSessionLocal is None:
        raise HTTPException(status_code=500, detail="Database not initialized")

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def get_llm_factory() -> LLMFactory:
    """
    Dependency that provides the shared LLMFactory instance.
    This is a singleton-like pattern for performance.
    """
    return llm_factory

async def get_audit_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> SQLAlchemyRepository:
    """
    Dependency that provides an instance of the audit repository.
    Example of hierarchical dependencies (depends on get_db_session).
    """
    # Import models here to avoid circular imports
    from ..models.audit import AuditLog, AuditLogSQL

    return SQLAlchemyRepository(session, AuditLogSQL, AuditLog)

class DocumentGenerationService:
    """
    Service class that orchestrates document generation.
    Injected via dependencies in FastAPI endpoints.
    """

    def __init__(
        self,
        factory: LLMFactory,
        audit_repo: Optional[SQLAlchemyRepository] = None
    ):
        self.factory = factory
        self.audit_repo = audit_repo

    async def generate_document(
        self,
        request: DocumentGenerationRequest
    ) -> DocumentGenerationResponse:
        """Core business logic for document generation."""
        # Select optimal LLM strategy based on complexity
        strategy = self.factory.get_optimal_strategy(
            task_complexity=request.complexity,
            max_cost_per_1k_tokens=(request.max_cost / 100) if request.max_cost else None
        )

        # Generate document using selected strategy
        prompt = self._build_prompt(request.document_type)
        result = await strategy.generate(prompt, request.user_idea)

        # Audit logging if repository available
        if self.audit_repo:
            await self._log_generation(request, result)

        return DocumentGenerationResponse(
            document_id=f"doc_{hash(request.user_idea) % 1000000}",
            content=result.content,
            cost=result.cost,
            provider_used=result.provider,
            generation_time_ms=result.generation_time_ms
        )

    def _build_prompt(self, doc_type: str) -> str:
        """Builds the appropriate prompt based on document type."""
        prompts = {
            "brd": "Generate a Business Requirement Document with the following sections...",
            "prd": "Generate a Product Requirement Document with technical specifications...",
            "both": "Generate both BRD and PRD documents..."
        }
        return prompts.get(doc_type, prompts["both"])

    async def _log_generation(self, request, result):
        """Log the generation request and result for auditing."""
        # Implementation depends on your audit log model
        pass

async def get_document_service(
    factory: Annotated[LLMFactory, Depends(get_llm_factory)],
    audit_repo: Annotated[SQLAlchemyRepository, Depends(get_audit_repository)]
) -> DocumentGenerationService:
    """
    Dependency that provides the document generation service.
    Demonstrates composition of multiple dependencies.
    """
    return DocumentGenerationService(factory, audit_repo)

# --- Example FastAPI Application ---
app = FastAPI(title="BRD/PRD Generator API")

@app.on_event("startup")
async def startup_event():
    """Initialize resources at application startup."""
    init_db()
    print("Database initialized")

@app.post("/generate", response_model=DocumentGenerationResponse)
async def generate_document(
    request: DocumentGenerationRequest,
    service: Annotated[DocumentGenerationService, Depends(get_document_service)]
):
    """
    Main API endpoint for document generation.
    All dependencies are injected automatically by FastAPI.
    """
    try:
        result = await service.generate_document(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

# --- Testing Override Example ---
def get_mock_service() -> DocumentGenerationService:
    """Mock service for testing - overrides the real dependency."""
    mock_factory = LLMFactory()  # Could be a mock object
    return DocumentGenerationService(mock_factory, None)

# In tests, you would use: app.dependency_overrides[get_document_service] = get_mock_service

from typing import Literal  # Add this import for Literal type