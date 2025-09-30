"""
FastAPI endpoints for BRD/PRD document generation.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Query
from fastapi.responses import JSONResponse
import asyncio
import logging
from datetime import datetime

from ..core.models import (
    GenerationRequest,
    GenerationResponse,
    DocumentType,
    ValidationResult,
    ComplexityLevel
)
from ..core.exceptions import (
    LLMCostExceededError,
    DocumentNotFoundError,
    ValidationError
)
from .dependencies import (
    GeneratorDep,
    RepositoryDep,
    ClientIdDep,
    ValidatorDep,
    ws_manager
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["documents"])


@router.post("/generate", response_model=GenerationResponse)
async def generate_document(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    generator: GeneratorDep,
    client_id: ClientIdDep
) -> GenerationResponse:
    """
    Generate BRD and/or PRD documents from user idea.

    Args:
        request: Generation request with user idea
        background_tasks: FastAPI background tasks
        generator: Document generator instance
        client_id: Authenticated client ID

    Returns:
        Generation response with documents and metadata

    Raises:
        HTTPException: On generation failure
    """
    try:
        logger.info(f"Document generation request from client: {client_id}")

        # Add client tracking
        request.additional_context = request.additional_context or {}
        request.additional_context["client_id"] = client_id
        request.additional_context["request_time"] = datetime.now().isoformat()

        # Generate documents
        response = await generator.generate(request)

        # Send WebSocket notification if connected
        await ws_manager.send_message(client_id, {
            "event": "generation_complete",
            "request_id": response.request_id,
            "status": response.status
        })

        return response

    except LLMCostExceededError as e:
        logger.error(f"Cost exceeded: {str(e)}")
        raise HTTPException(
            status_code=402,  # Payment Required
            detail=f"Generation cost would exceed limit: {str(e)}"
        )
    except ValidationError as e:
        logger.error(f"Validation failed: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=f"Document validation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Document generation failed: {str(e)}"
        )


@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    repository: RepositoryDep,
    client_id: ClientIdDep
) -> Dict[str, Any]:
    """
    Retrieve a document by ID.

    Args:
        document_id: Document ID (BRD-XXXXXX or PRD-XXXXXX)
        repository: Repository instance
        client_id: Authenticated client ID

    Returns:
        Document with metadata

    Raises:
        HTTPException: If document not found
    """
    try:
        # Determine document type
        if document_id.startswith("BRD"):
            document = await repository.get_brd(document_id)
            doc_type = "BRD"
        elif document_id.startswith("PRD"):
            document = await repository.get_prd(document_id)
            doc_type = "PRD"
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid document ID format: {document_id}"
            )

        return {
            "document_type": doc_type,
            "document": document.model_dump(),
            "retrieved_at": datetime.now().isoformat()
        }

    except DocumentNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found"
        )
    except Exception as e:
        logger.error(f"Failed to retrieve document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve document: {str(e)}"
        )


@router.get("/documents")
async def list_documents(
    document_type: Optional[DocumentType] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repository: RepositoryDep = None,
    client_id: ClientIdDep = None
) -> Dict[str, Any]:
    """
    List documents with optional filtering.

    Args:
        document_type: Filter by document type
        limit: Maximum documents to return
        offset: Number of documents to skip
        repository: Repository instance
        client_id: Authenticated client ID

    Returns:
        List of documents with metadata
    """
    try:
        documents = []

        if document_type in [DocumentType.BRD, None]:
            brds = await repository.list_brds(limit=limit, offset=offset)
            documents.extend([
                {"type": "BRD", "document": brd.model_dump()}
                for brd in brds
            ])

        if document_type in [DocumentType.PRD, None]:
            prds = await repository.list_prds(limit=limit, offset=offset)
            documents.extend([
                {"type": "PRD", "document": prd.model_dump()}
                for prd in prds
            ])

        return {
            "total": len(documents),
            "limit": limit,
            "offset": offset,
            "documents": documents
        }

    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.post("/validate/{document_id}", response_model=ValidationResult)
async def validate_document(
    document_id: str,
    validator: ValidatorDep,
    repository: RepositoryDep,
    client_id: ClientIdDep
) -> ValidationResult:
    """
    Validate an existing document.

    Args:
        document_id: Document ID to validate
        validator: Document validator instance
        repository: Repository instance
        client_id: Authenticated client ID

    Returns:
        Validation result with issues and recommendations

    Raises:
        HTTPException: If document not found or validation fails
    """
    try:
        # Get document
        if document_id.startswith("BRD"):
            document = await repository.get_brd(document_id)
            result = await validator.validate_brd(document)
        elif document_id.startswith("PRD"):
            document = await repository.get_prd(document_id)
            result = await validator.validate_prd(document)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid document ID format: {document_id}"
            )

        # Store validation result
        await repository.save_validation_result(result)

        return result

    except DocumentNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found"
        )
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


@router.post("/regenerate/{document_id}", response_model=GenerationResponse)
async def regenerate_document(
    document_id: str,
    improvements: Optional[str] = None,
    generator: GeneratorDep = None,
    client_id: ClientIdDep = None
) -> GenerationResponse:
    """
    Regenerate a document with improvements.

    Args:
        document_id: Document ID to regenerate
        improvements: Optional improvement instructions
        generator: Document generator instance
        client_id: Authenticated client ID

    Returns:
        New generation response

    Raises:
        HTTPException: If regeneration fails
    """
    try:
        response = await generator.regenerate(document_id, improvements)

        # Send WebSocket notification
        await ws_manager.send_message(client_id, {
            "event": "regeneration_complete",
            "original_document_id": document_id,
            "new_request_id": response.request_id,
            "status": response.status
        })

        return response

    except DocumentNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found"
        )
    except Exception as e:
        logger.error(f"Regeneration failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Document regeneration failed: {str(e)}"
        )


@router.get("/search")
async def search_documents(
    query: str = Query(..., min_length=3),
    document_type: Optional[DocumentType] = None,
    limit: int = Query(100, ge=1, le=500),
    repository: RepositoryDep = None,
    client_id: ClientIdDep = None
) -> List[Dict[str, Any]]:
    """
    Search for documents by text query.

    Args:
        query: Search query string
        document_type: Filter by document type
        limit: Maximum results
        repository: Repository instance
        client_id: Authenticated client ID

    Returns:
        Search results with relevance
    """
    try:
        results = await repository.search(
            query=query,
            document_type=document_type,
            limit=limit
        )
        return results

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str
):
    """
    WebSocket endpoint for real-time updates.

    Args:
        websocket: WebSocket connection
        client_id: Client identifier
    """
    await ws_manager.connect(client_id, websocket)
    logger.info(f"WebSocket connected: {client_id}")

    try:
        # Send initial connection message
        await websocket.send_json({
            "event": "connected",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        })

        # Keep connection alive
        while True:
            # Wait for messages from client
            data = await websocket.receive_json()

            # Handle different message types
            if data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            elif data.get("type") == "status":
                # Could check generation status here
                request_id = data.get("request_id")
                await websocket.send_json({
                    "type": "status_update",
                    "request_id": request_id,
                    "status": "processing"  # Would check actual status
                })

    except WebSocketDisconnect:
        await ws_manager.disconnect(client_id)
        logger.info(f"WebSocket disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await ws_manager.disconnect(client_id)


@router.get("/history/{document_id}")
async def get_document_history(
    document_id: str,
    repository: RepositoryDep,
    client_id: ClientIdDep
) -> List[Dict[str, Any]]:
    """
    Get generation history for a document.

    Args:
        document_id: Document ID
        repository: Repository instance
        client_id: Authenticated client ID

    Returns:
        List of history entries
    """
    try:
        history = await repository.get_document_history(document_id)
        return history

    except DocumentNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found"
        )
    except Exception as e:
        logger.error(f"Failed to get history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document history: {str(e)}"
        )


# Health check endpoints
@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/health/detailed")
async def detailed_health_check(
    generator: GeneratorDep,
    repository: RepositoryDep
) -> Dict[str, Any]:
    """
    Detailed health check with component status.

    Returns:
        Detailed health status of all components
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }

    # Check LLM factory
    try:
        providers = generator.llm_factory.get_available_providers()
        health_status["components"]["llm_factory"] = {
            "status": "healthy",
            "available_providers": providers
        }
    except Exception as e:
        health_status["components"]["llm_factory"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    # Check repository
    try:
        # Simple check - try to list documents
        await repository.list_brds(limit=1)
        health_status["components"]["repository"] = {
            "status": "healthy"
        }
    except Exception as e:
        health_status["components"]["repository"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    # Check WebSocket connections
    health_status["components"]["websocket"] = {
        "status": "healthy",
        "active_connections": len(ws_manager.active_connections)
    }

    return health_status