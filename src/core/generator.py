"""
Document Generation Service with async orchestration.

This module provides the main document generation logic, coordinating
between LLM providers, validation, and storage.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import json

from ..core.models import (
    GenerationRequest,
    GenerationResponse,
    BRDDocument,
    PRDDocument,
    DocumentType,
    ComplexityLevel,
    CostMetadata,
    ValidationResult,
    ValidationStatus,
    ValidationIssue
)
from ..core.exceptions import (
    LLMCostExceededError,
    ValidationError,
    DocumentValidationError,
    SMARTCriteriaError
)
from ..llm import (
    LLMFactory,
    get_llm_factory,
    ProviderName,
    TaskComplexity
)
from ..repository import (
    BaseRepository,
    get_repository
)
from .validator import DocumentValidator
from .prompts import PromptBuilder

logger = logging.getLogger(__name__)


class DocumentGenerator:
    """
    Main document generation service.

    Orchestrates the entire document generation process including:
    - LLM provider selection
    - Document generation
    - Validation
    - Storage
    - Cost tracking
    """

    def __init__(
        self,
        llm_factory: Optional[LLMFactory] = None,
        repository: Optional[BaseRepository] = None,
        validator: Optional[DocumentValidator] = None,
        prompt_builder: Optional[PromptBuilder] = None
    ):
        """
        Initialize document generator.

        Args:
            llm_factory: LLM factory instance
            repository: Repository for storage
            validator: Document validator
            prompt_builder: Prompt builder for templates
        """
        self.llm_factory = llm_factory or get_llm_factory()
        self.repository = repository or get_repository()
        self.validator = validator or DocumentValidator()
        self.prompt_builder = prompt_builder or PromptBuilder()

    async def generate(
        self,
        request: GenerationRequest
    ) -> GenerationResponse:
        """
        Generate documents based on request.

        Args:
            request: Generation request with user idea

        Returns:
            Generation response with documents and metadata

        Raises:
            LLMCostExceededError: If cost exceeds limit
            ValidationError: If validation fails
        """
        logger.info(f"Starting document generation for type: {request.document_type}")

        # Initialize response
        response = GenerationResponse(
            request_id=f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            status="processing",
            generation_metadata={
                "created_at": datetime.now().isoformat(),
                "document_type": request.document_type.value,
                "complexity": request.complexity.value if request.complexity else "moderate"
            },
            cost_breakdown={}
        )

        try:
            # Process based on document type
            if request.document_type == DocumentType.BRD:
                brd, brd_cost = await self._generate_brd(request)
                response.brd_document = brd
                response.cost_breakdown = {
                    "brd_cost": brd_cost.total_cost,
                    "total_cost": brd_cost.total_cost
                }
                response.generation_metadata["cost_metadata"] = brd_cost.model_dump()

            elif request.document_type == DocumentType.PRD:
                prd, prd_cost = await self._generate_prd(request)
                response.prd_document = prd
                response.cost_breakdown = {
                    "prd_cost": prd_cost.total_cost,
                    "total_cost": prd_cost.total_cost
                }
                response.generation_metadata["cost_metadata"] = prd_cost.model_dump()

            else:  # BOTH
                # Generate BRD first
                brd, brd_cost = await self._generate_brd(request)
                response.brd_document = brd

                # Generate PRD with BRD context
                prd, prd_cost = await self._generate_prd(request, brd)
                response.prd_document = prd

                # Combine costs
                combined_cost = self._combine_costs(brd_cost, prd_cost)
                response.cost_breakdown = {
                    "brd_cost": brd_cost.total_cost,
                    "prd_cost": prd_cost.total_cost,
                    "total_cost": combined_cost.total_cost
                }
                response.generation_metadata["cost_metadata"] = combined_cost.model_dump()

            # Validate documents
            await self._validate_and_store(response)

            # Update status
            response.status = "completed"
            response.generation_metadata["completed_at"] = datetime.now().isoformat()

            # Save generation history
            await self.repository.save_generation_history(request, response)

            logger.info(f"Document generation completed: {response.request_id}")
            return response

        except Exception as e:
            logger.error(f"Document generation failed: {str(e)}")
            response.status = "failed"
            response.error_message = str(e)
            raise

    async def _generate_brd(
        self,
        request: GenerationRequest,
        chunk_size: int = 3000
    ) -> Tuple[BRDDocument, CostMetadata]:
        """
        Generate BRD document.

        Args:
            request: Generation request
            chunk_size: Maximum chunk size for input

        Returns:
            Tuple of (BRDDocument, CostMetadata)
        """
        logger.info("Generating BRD document")

        # Chunk input if too large
        idea_chunks = self._chunk_text(request.user_idea, chunk_size)

        # Select LLM provider
        strategy = self.llm_factory.create_strategy(
            complexity=request.complexity,
            user_idea=request.user_idea,
            document_type=DocumentType.BRD,
            max_cost=request.max_cost
        )

        # Process chunks if needed
        if len(idea_chunks) > 1:
            logger.info(f"Processing {len(idea_chunks)} chunks")
            # For multiple chunks, process first chunk in detail
            # and summarize remaining chunks
            main_idea = idea_chunks[0]
            additional_context = "\n\nAdditional context:\n" + "\n".join(
                f"- {self._summarize_chunk(chunk)}" for chunk in idea_chunks[1:]
            )
            processed_idea = main_idea + additional_context
        else:
            processed_idea = request.user_idea

        # Create enhanced request with processed idea
        enhanced_request = GenerationRequest(
            user_idea=processed_idea,
            document_type=DocumentType.BRD,
            complexity=request.complexity,
            max_cost=request.max_cost,
            additional_context=request.additional_context
        )

        # Generate BRD
        brd_document, cost_metadata = await strategy.generate_brd(enhanced_request)

        # Ensure document has required fields
        if not brd_document.document_id:
            brd_document.document_id = f"BRD-{datetime.now().strftime('%H%M%S')}"

        if not brd_document.created_date:
            brd_document.created_date = datetime.now().isoformat()

        brd_document.last_modified = datetime.now().isoformat()

        logger.info(f"BRD generated: {brd_document.document_id}, cost: ${cost_metadata.total_cost:.4f}")
        return brd_document, cost_metadata

    async def _generate_prd(
        self,
        request: GenerationRequest,
        brd_document: Optional[BRDDocument] = None,
        chunk_size: int = 3000
    ) -> Tuple[PRDDocument, CostMetadata]:
        """
        Generate PRD document.

        Args:
            request: Generation request
            brd_document: Optional BRD for context
            chunk_size: Maximum chunk size for input

        Returns:
            Tuple of (PRDDocument, CostMetadata)
        """
        logger.info("Generating PRD document")

        # Chunk input if too large
        idea_chunks = self._chunk_text(request.user_idea, chunk_size)

        # Select LLM provider
        strategy = self.llm_factory.create_strategy(
            complexity=request.complexity or ComplexityLevel.MODERATE,
            user_idea=request.user_idea,
            document_type=DocumentType.PRD,
            max_cost=request.max_cost
        )

        # Process chunks if needed
        if len(idea_chunks) > 1:
            processed_idea = idea_chunks[0] + "\n\nAdditional context:\n" + "\n".join(
                f"- {self._summarize_chunk(chunk)}" for chunk in idea_chunks[1:]
            )
        else:
            processed_idea = request.user_idea

        # Create enhanced request
        enhanced_request = GenerationRequest(
            user_idea=processed_idea,
            document_type=DocumentType.PRD,
            complexity=request.complexity,
            max_cost=request.max_cost,
            additional_context=request.additional_context
        )

        # Generate PRD
        prd_document, cost_metadata = await strategy.generate_prd(
            enhanced_request,
            brd_document
        )

        # Ensure document has required fields
        if not prd_document.document_id:
            prd_document.document_id = f"PRD-{datetime.now().strftime('%H%M%S')}"

        if not prd_document.created_date:
            prd_document.created_date = datetime.now().isoformat()

        prd_document.last_modified = datetime.now().isoformat()

        # Link to BRD if provided
        if brd_document:
            prd_document.related_brd_id = brd_document.document_id

        logger.info(f"PRD generated: {prd_document.document_id}, cost: ${cost_metadata.total_cost:.4f}")
        return prd_document, cost_metadata

    def _chunk_text(self, text: str, chunk_size: int) -> list[str]:
        """
        Split text into chunks for processing.

        Args:
            text: Text to chunk
            chunk_size: Maximum chunk size

        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        words = text.split()
        current_chunk = []
        current_size = 0

        for word in words:
            word_size = len(word) + 1  # +1 for space
            if current_size + word_size > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_size = word_size
            else:
                current_chunk.append(word)
                current_size += word_size

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _summarize_chunk(self, chunk: str, max_length: int = 200) -> str:
        """
        Create a summary of a text chunk.

        Args:
            chunk: Text chunk to summarize
            max_length: Maximum summary length

        Returns:
            Summarized text
        """
        # Simple summarization - take first and last parts
        if len(chunk) <= max_length:
            return chunk

        half_length = max_length // 2 - 10  # Reserve space for ellipsis
        return f"{chunk[:half_length]}... {chunk[-half_length:]}"

    def _combine_costs(
        self,
        cost1: CostMetadata,
        cost2: CostMetadata
    ) -> CostMetadata:
        """
        Combine two cost metadata objects.

        Args:
            cost1: First cost metadata
            cost2: Second cost metadata

        Returns:
            Combined cost metadata
        """
        return CostMetadata(
            provider=f"{cost1.provider}+{cost2.provider}",
            model_name=f"{cost1.model_name}+{cost2.model_name}",
            input_tokens=cost1.input_tokens + cost2.input_tokens,
            output_tokens=cost1.output_tokens + cost2.output_tokens,
            cost_per_1k_input=(cost1.cost_per_1k_input + cost2.cost_per_1k_input) / 2,
            cost_per_1k_output=(cost1.cost_per_1k_output + cost2.cost_per_1k_output) / 2,
            total_cost=cost1.total_cost + cost2.total_cost,
            generation_time_ms=cost1.generation_time_ms + cost2.generation_time_ms,
            cached=cost1.cached or cost2.cached
        )

    async def _validate_and_store(self, response: GenerationResponse):
        """
        Validate and store generated documents.

        Args:
            response: Generation response with documents
        """
        # Validate BRD if present
        if response.brd_document:
            brd_validation = await self.validator.validate_brd(response.brd_document)

            if not brd_validation.is_valid:
                raise DocumentValidationError(
                    f"BRD validation failed: {brd_validation.issues}"
                )

            # Store BRD
            try:
                await self.repository.save_brd(response.brd_document)
                logger.info(f"Stored BRD: {response.brd_document.document_id}")
            except Exception as e:
                logger.warning(f"Failed to store BRD: {e}")

            # Store validation result
            await self.repository.save_validation_result(brd_validation)

        # Validate PRD if present
        if response.prd_document:
            prd_validation = await self.validator.validate_prd(response.prd_document)

            if not prd_validation.is_valid:
                raise DocumentValidationError(
                    f"PRD validation failed: {prd_validation.issues}"
                )

            # Store PRD
            try:
                await self.repository.save_prd(response.prd_document)
                logger.info(f"Stored PRD: {response.prd_document.document_id}")
            except Exception as e:
                logger.warning(f"Failed to store PRD: {e}")

            # Store validation result
            await self.repository.save_validation_result(prd_validation)

    async def regenerate(
        self,
        document_id: str,
        improvements: Optional[str] = None
    ) -> GenerationResponse:
        """
        Regenerate a document with improvements.

        Args:
            document_id: Document ID to regenerate
            improvements: Optional improvement instructions

        Returns:
            New generation response
        """
        # Get existing document
        linked_docs = await self.repository.get_linked_documents(document_id)

        if not linked_docs["brd"] and not linked_docs["prd"]:
            raise DocumentValidationError(f"Document {document_id} not found")

        # Create new request based on existing document
        if linked_docs["brd"]:
            original_idea = linked_docs["brd"].business_context
        else:
            original_idea = linked_docs["prd"].product_overview

        # Add improvements to idea
        if improvements:
            enhanced_idea = f"{original_idea}\n\nImprovements requested:\n{improvements}"
        else:
            enhanced_idea = original_idea

        # Determine document type
        if document_id.startswith("BRD"):
            doc_type = DocumentType.BRD
        elif document_id.startswith("PRD"):
            doc_type = DocumentType.PRD
        else:
            doc_type = DocumentType.BOTH

        # Create new request
        request = GenerationRequest(
            user_idea=enhanced_idea,
            document_type=doc_type,
            complexity=ComplexityLevel.MODERATE
        )

        # Generate new version
        return await self.generate(request)

    async def get_generation_status(
        self,
        request_id: str
    ) -> Dict[str, Any]:
        """
        Get status of a generation request.

        Args:
            request_id: Request ID

        Returns:
            Status information
        """
        # This would typically check a job queue or database
        # For now, return a simple status
        return {
            "request_id": request_id,
            "status": "completed",
            "message": "Document generation completed"
        }