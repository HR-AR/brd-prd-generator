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
    ComplexityLevel,
    BRDDocument,
    PRDDocument
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


@router.post("/generate-test", response_model=GenerationResponse)
async def generate_test_document(
    request: GenerationRequest,
    client_id: ClientIdDep
) -> GenerationResponse:
    """
    Test endpoint that returns mock BRD/PRD documents without calling LLMs.
    Use this for testing the UI when LLM APIs are not configured.
    """
    from ..core.models import (
        BRDDocument, PRDDocument, BusinessObjective, UserStory,
        TechnicalRequirement, Stakeholder,
        ValidationStatus, Priority, CostMetadata
    )
    import random

    # Generate mock BRD if requested
    brd_doc = None
    if request.document_type in [DocumentType.BRD, DocumentType.BOTH]:
        brd_doc = BRDDocument(
            document_id=f"BRD-{random.randint(100000, 999999)}",
            title="Water Intake Tracking Mobile Application",
            problem_statement="Users struggle to maintain proper hydration levels throughout the day, leading to decreased health and productivity. Current solutions lack proper tracking, reminders, and personalized insights that adapt to individual needs and lifestyles.",
            executive_summary="A comprehensive mobile application designed to revolutionize personal hydration management by providing intelligent tracking, personalized reminders, and actionable insights. The solution targets health-conscious individuals aged 25-45 seeking to improve their daily water intake habits through data-driven approaches and behavioral science principles.",
            business_context="The global health and wellness market is experiencing rapid growth at 15% CAGR, with digital health applications showing particularly strong adoption among millennials and Gen Z consumers. Hydration apps represent a growing $500M segment with increasing demand for personalized health solutions. Market research indicates significant opportunity for differentiation through AI-driven personalization and gamification features.",
            objectives=[
                BusinessObjective(
                    objective_id=f"OBJ-{random.randint(100, 999):03d}",
                    description="Achieve 25,000 daily active users within 6 months of launch, representing a 40% increase over industry benchmarks for health tracking applications",
                    success_criteria=[
                        "Reach 25,000 DAU milestone by end of month 6",
                        "Maintain 70% user retention rate after 30 days",
                        "Achieve average session duration of 3+ minutes per user"
                    ],
                    business_value="Increased user engagement drives higher retention rates, enabling premium subscription conversions estimated at $200K annual recurring revenue by year 1",
                    priority=Priority.HIGH,
                    kpi_metrics=["Daily Active Users (DAU)", "30-day Retention Rate", "Average Session Duration"]
                )
            ],
            scope={
                "in_scope": [
                    "Water intake logging and tracking functionality",
                    "Personalized reminder system based on user patterns",
                    "Progress analytics and data visualizations",
                    "Goal setting and achievement tracking",
                    "Integration with Apple Health and Google Fit"
                ],
                "out_of_scope": [
                    "Meal and nutrition tracking features",
                    "Exercise and fitness tracking capabilities",
                    "Social networking and community features",
                    "E-commerce and product sales functionality"
                ]
            },
            stakeholders=[
                Stakeholder(
                    name="Product Owner",
                    role="Strategic decision maker and business sponsor, responsible for ROI and product vision",
                    interest_level="high",
                    influence_level="high"
                ),
                Stakeholder(
                    name="Engineering Lead",
                    role="Technical architecture design, development oversight, and technology stack decisions",
                    interest_level="high",
                    influence_level="high"
                )
            ],
            success_metrics=[
                "User Retention: 70% retention rate after 30 days",
                "Daily Active Users: 25,000+ within 6 months",
                "App Store Rating: Maintain 4.5+ star rating across platforms",
                "Conversion Rate: 10% free-to-premium conversion within 90 days"
            ],
            assumptions=[
                "Users have access to smartphones running iOS 14+ or Android 10+",
                "Users are intrinsically motivated to track hydration habits",
                "App store approval processes complete within 2 weeks of submission"
            ],
            constraints=[
                "Development budget capped at $150,000 for MVP",
                "MVP launch timeline of 6 months from project kickoff",
                "Must comply with HIPAA and GDPR data privacy regulations"
            ],
            risks=[
                {
                    "risk": "Low user adoption due to high market competition",
                    "impact": "high",
                    "mitigation": "Implement aggressive marketing campaign focusing on unique features"
                }
            ]
        )

    # Generate mock PRD if requested
    prd_doc = None
    if request.document_type in [DocumentType.PRD, DocumentType.BOTH]:
        prd_doc = PRDDocument(
            document_id=f"PRD-{random.randint(100000, 999999)}",
            related_brd_id=brd_doc.document_id if brd_doc else None,
            product_name="HydroTrack: Smart Water Intake Companion",
            product_vision="To become the world's most intelligent hydration tracking platform, helping millions achieve optimal health through personalized water intake management.",
            target_audience=[
                "Health-conscious millennials aged 25-35",
                "Fitness enthusiasts seeking performance optimization",
                "Office workers with sedentary lifestyles"
            ],
            value_proposition="HydroTrack combines AI-driven personalization with behavioral science to deliver smart reminders and insights that adapt to your lifestyle.",
            user_stories=[
                UserStory(
                    story_id=f"US-{random.randint(100, 999):03d}",
                    story="As a health-conscious user, I want to quickly log my water intake throughout the day so that I can track my progress toward my daily hydration goal",
                    acceptance_criteria=[
                        "User can log water intake with one tap",
                        "Custom amounts can be entered via number pad",
                        "Daily total updates in real-time"
                    ],
                    priority=Priority.HIGH,
                    story_points=5,
                    dependencies=[]
                )
            ],
            features=[
                {
                    "feature_id": "FEAT-001",
                    "name": "Quick Log Water Intake",
                    "description": "One-tap logging with smart defaults",
                    "priority": "high"
                }
            ],
            technical_requirements=[
                TechnicalRequirement(
                    requirement_id=f"TR-{random.randint(100, 999):03d}",
                    category="architecture",
                    description="Implement cloud-based backend architecture using microservices pattern for scalability and maintainability with auto-scaling capabilities",
                    technology_stack=["Node.js", "Express", "MongoDB", "AWS Lambda"],
                    constraints=["Must support 100k concurrent users"]
                )
            ],
            technology_stack=["React Native", "TypeScript", "Node.js", "MongoDB", "AWS"],
            acceptance_criteria=[
                "All core features functional on both iOS and Android",
                "99.9% crash-free user rate"
            ],
            metrics_and_kpis=[
                "Daily Active Users (DAU)",
                "User Retention (Day 1, Day 7, Day 30)",
                "Premium Conversion Rate"
            ]
        )

    # Create response
    response = GenerationResponse(
        request_id=f"REQ-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        status="completed",
        brd_document=brd_doc,
        prd_document=prd_doc,
        validation_results=ValidationResult(
            document_id=brd_doc.document_id if brd_doc else (prd_doc.document_id if prd_doc else "TEST-000000"),
            document_type=DocumentType.BRD if brd_doc else DocumentType.PRD,
            overall_status=ValidationStatus.PASSED,
            quality_score=95.0,
            issues=[],
            smart_criteria_check=ValidationStatus.PASSED,
            completeness_check=ValidationStatus.PASSED,
            consistency_check=ValidationStatus.PASSED,
            word_count=1500,
            readability_score=85.0,
            recommendations=["Consider adding more KPIs", "Include more specific metrics in objectives"]
        ) if (brd_doc or prd_doc) else None,
        generation_metadata={
            "test_mode": True,
            "generated_at": datetime.now().isoformat()
        },
        cost_breakdown={
            "total_cost": 0.0112,
            "brd_cost": 0.005 if brd_doc else 0.0,
            "prd_cost": 0.0062 if prd_doc else 0.0,
            "generation_time_ms": 220.0
        }
    )

    logger.info(f"Test document generated for client: {client_id}")
    return response


@router.post("/generate-prompt")
async def generate_prompt(
    brd_document: Optional[BRDDocument] = None,
    prd_document: Optional[PRDDocument] = None,
    client_id: ClientIdDep = None
) -> Dict[str, Any]:
    """
    Generate a Claude prompt from the reviewed BRD and PRD documents.
    This prompt can be used to create the actual implementation.
    """
    if not brd_document and not prd_document:
        raise HTTPException(
            status_code=400,
            detail="At least one document (BRD or PRD) must be provided"
        )

    prompt_parts = []

    # Start with context
    prompt_parts.append("# Project Implementation Request\n")

    if brd_document:
        prompt_parts.append("## Business Requirements (from BRD)\n")
        prompt_parts.append(f"**Title:** {brd_document.title}\n")
        prompt_parts.append(f"**Problem Statement:** {brd_document.problem_statement}\n")
        prompt_parts.append(f"**Executive Summary:** {brd_document.executive_summary}\n")

        if brd_document.objectives:
            prompt_parts.append("\n### Business Objectives\n")
            for obj in brd_document.objectives:
                prompt_parts.append(f"- {obj.description} (Priority: {obj.priority})\n")

        if brd_document.success_metrics:
            prompt_parts.append("\n### Success Metrics\n")
            for metric in brd_document.success_metrics:
                prompt_parts.append(f"- {metric}\n")

    if prd_document:
        prompt_parts.append("\n## Product Requirements (from PRD)\n")
        prompt_parts.append(f"**Product Overview:** {prd_document.product_overview}\n")
        prompt_parts.append(f"**Target Audience:** {prd_document.target_audience}\n")

        if prd_document.user_stories:
            prompt_parts.append("\n### User Stories\n")
            for story in prd_document.user_stories[:5]:  # Top 5 stories
                prompt_parts.append(f"- As a user, {story.description} (Priority: {story.priority})\n")

        if prd_document.technical_requirements:
            prompt_parts.append("\n### Technical Requirements\n")
            for req in prd_document.technical_requirements:
                prompt_parts.append(f"- {req.description} ({req.category})\n")

    # Add implementation request
    prompt_parts.append("\n## Implementation Request\n")
    prompt_parts.append("Please help me implement this project by:\n")
    prompt_parts.append("1. Creating the initial project structure\n")
    prompt_parts.append("2. Setting up the core architecture\n")
    prompt_parts.append("3. Implementing the main features\n")
    prompt_parts.append("4. Adding necessary tests\n")
    prompt_parts.append("5. Providing deployment instructions\n")

    prompt_parts.append("\nPlease start with the project setup and architecture.")

    prompt = "".join(prompt_parts)

    return {
        "prompt": prompt,
        "metadata": {
            "has_brd": brd_document is not None,
            "has_prd": prd_document is not None,
            "prompt_length": len(prompt),
            "generated_at": datetime.now().isoformat()
        }
    }