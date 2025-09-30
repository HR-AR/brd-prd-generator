"""
Multi-LLM Sequential Document Generator

Implements a sophisticated multi-pass generation approach:
1. Gemini (Draft) - Fast initial draft with broad context
2. GPT-4 (Refine) - Detailed enhancement and structure improvement
3. Claude (Polish) - Final polish for clarity and professional quality

Each LLM builds upon the previous output, resulting in higher quality documents.
"""

import asyncio
import logging
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

from ..core.models import (
    GenerationRequest,
    BRDDocument,
    PRDDocument,
    DocumentType,
    CostMetadata
)
from ..llm import LLMFactory, ProviderName
from ..llm.client import LLMConfig
from ..llm.openai_strategy import OpenAIStrategy
from ..llm.claude_strategy import ClaudeStrategy
from ..llm.gemini_strategy import GeminiStrategy

logger = logging.getLogger(__name__)


class MultiLLMGenerator:
    """
    Multi-LLM sequential generator for high-quality document generation.

    Strategy:
    - Gemini: Fast, creative initial draft
    - GPT-4: Detailed refinement and enhancement
    - Claude: Final polish for professional quality
    """

    def __init__(self, llm_factory: LLMFactory):
        """Initialize with LLM factory."""
        self.llm_factory = llm_factory

    async def generate_brd_sequential(
        self,
        request: GenerationRequest
    ) -> Tuple[BRDDocument, CostMetadata]:
        """
        Generate BRD using sequential multi-LLM approach.

        Process:
        1. Gemini creates initial draft
        2. GPT-4 refines and enhances
        3. Claude polishes for final quality

        Returns:
            Final BRD document and combined cost metadata
        """
        logger.info("Starting multi-LLM BRD generation: Gemini → GPT-4 → Claude")

        total_cost = 0.0
        costs_by_provider = {}

        # Phase 1: Gemini Draft
        logger.info("Phase 1/3: Gemini generating initial BRD draft...")
        gemini_config_dict = self.llm_factory._DEFAULT_CONFIGS[ProviderName.GEMINI].copy()
        gemini_api_key = self.llm_factory._get_api_key(ProviderName.GEMINI)
        gemini_config = LLMConfig(api_key=gemini_api_key, **gemini_config_dict)
        gemini_strategy = GeminiStrategy(gemini_config)
        gemini_doc, gemini_cost = await gemini_strategy.generate_brd(request)
        total_cost += gemini_cost.total_cost
        costs_by_provider['gemini'] = gemini_cost.total_cost
        logger.info(f"✓ Gemini draft complete - Cost: ${gemini_cost.total_cost:.4f}")

        # Phase 2: GPT-4 Refinement
        logger.info("Phase 2/3: GPT-4 refining and enhancing BRD...")
        refinement_request = self._create_refinement_request(
            original_request=request,
            previous_doc=gemini_doc,
            refinement_instructions="Enhance the BRD with: (1) More specific SMART criteria, (2) Detailed success metrics with quantifiable targets, (3) Comprehensive risk analysis, (4) Clearer scope boundaries"
        )
        openai_config_dict = self.llm_factory._DEFAULT_CONFIGS[ProviderName.OPENAI].copy()
        openai_api_key = self.llm_factory._get_api_key(ProviderName.OPENAI)
        openai_config = LLMConfig(api_key=openai_api_key, **openai_config_dict)
        openai_strategy = OpenAIStrategy(openai_config)
        gpt_doc, gpt_cost = await openai_strategy.generate_brd(refinement_request)
        total_cost += gpt_cost.total_cost
        costs_by_provider['openai'] = gpt_cost.total_cost
        logger.info(f"✓ GPT-4 refinement complete - Cost: ${gpt_cost.total_cost:.4f}")

        # Phase 3: Claude Final Polish
        logger.info("Phase 3/3: Claude polishing final BRD...")
        polish_request = self._create_refinement_request(
            original_request=request,
            previous_doc=gpt_doc,
            refinement_instructions="Final polish: (1) Ensure executive summary is compelling and concise, (2) Verify all objectives follow SMART criteria, (3) Add clarity and professional tone, (4) Ensure consistency across all sections"
        )
        claude_config_dict = self.llm_factory._DEFAULT_CONFIGS[ProviderName.CLAUDE].copy()
        claude_api_key = self.llm_factory._get_api_key(ProviderName.CLAUDE)
        claude_config = LLMConfig(api_key=claude_api_key, **claude_config_dict)
        claude_strategy = ClaudeStrategy(claude_config)
        final_doc, claude_cost = await claude_strategy.generate_brd(polish_request)
        total_cost += claude_cost.total_cost
        costs_by_provider['claude'] = claude_cost.total_cost
        logger.info(f"✓ Claude polish complete - Cost: ${claude_cost.total_cost:.4f}")

        # Combine cost metadata
        total_input_tokens = gemini_cost.input_tokens + gpt_cost.input_tokens + claude_cost.input_tokens
        total_output_tokens = gemini_cost.output_tokens + gpt_cost.output_tokens + claude_cost.output_tokens
        total_tokens = total_input_tokens + total_output_tokens

        # Calculate weighted average cost per 1K tokens
        avg_cost_per_1k_input = (total_cost / (total_tokens / 1000)) if total_tokens > 0 else 0.0
        avg_cost_per_1k_output = avg_cost_per_1k_input  # Same for combined

        # Sum generation times
        total_gen_time = gemini_cost.generation_time_ms + gpt_cost.generation_time_ms + claude_cost.generation_time_ms

        combined_cost = CostMetadata(
            provider="multi-llm",
            model_name="gemini-2.0-flash-exp + gpt-4-turbo + claude-opus-4.1",
            total_cost=total_cost,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            cost_per_1k_input=avg_cost_per_1k_input,
            cost_per_1k_output=avg_cost_per_1k_output,
            generation_time_ms=total_gen_time,
            cached=False,
            breakdown=costs_by_provider
        )

        logger.info(f"Multi-LLM BRD generation complete - Total cost: ${total_cost:.4f}")
        return final_doc, combined_cost

    async def generate_prd_sequential(
        self,
        request: GenerationRequest,
        brd_document: Optional[BRDDocument] = None
    ) -> Tuple[PRDDocument, CostMetadata]:
        """
        Generate PRD using sequential multi-LLM approach.

        Process:
        1. Gemini creates initial draft with BRD context
        2. GPT-4 refines technical details and user stories
        3. Claude polishes for implementation readiness

        Returns:
            Final PRD document and combined cost metadata
        """
        logger.info("Starting multi-LLM PRD generation: Gemini → GPT-4 → Claude")

        total_cost = 0.0
        costs_by_provider = {}

        # Phase 1: Gemini Draft
        logger.info("Phase 1/3: Gemini generating initial PRD draft...")
        gemini_config_dict = self.llm_factory._DEFAULT_CONFIGS[ProviderName.GEMINI].copy()
        gemini_api_key = self.llm_factory._get_api_key(ProviderName.GEMINI)
        gemini_config = LLMConfig(api_key=gemini_api_key, **gemini_config_dict)
        gemini_strategy = GeminiStrategy(gemini_config)
        gemini_doc, gemini_cost = await gemini_strategy.generate_prd(request, brd_document)
        total_cost += gemini_cost.total_cost
        costs_by_provider['gemini'] = gemini_cost.total_cost
        logger.info(f"✓ Gemini draft complete - Cost: ${gemini_cost.total_cost:.4f}")

        # Phase 2: GPT-4 Technical Enhancement
        logger.info("Phase 2/3: GPT-4 enhancing technical details...")
        refinement_request = self._create_refinement_request(
            original_request=request,
            previous_doc=gemini_doc,
            refinement_instructions="Enhance PRD with: (1) More detailed user stories with acceptance criteria, (2) Comprehensive technical requirements, (3) Specific technology stack recommendations, (4) Detailed API specifications and data models, (5) Performance and scalability requirements"
        )
        openai_config_dict = self.llm_factory._DEFAULT_CONFIGS[ProviderName.OPENAI].copy()
        openai_api_key = self.llm_factory._get_api_key(ProviderName.OPENAI)
        openai_config = LLMConfig(api_key=openai_api_key, **openai_config_dict)
        openai_strategy = OpenAIStrategy(openai_config)
        gpt_doc, gpt_cost = await openai_strategy.generate_prd(refinement_request, brd_document)
        total_cost += gpt_cost.total_cost
        costs_by_provider['openai'] = gpt_cost.total_cost
        logger.info(f"✓ GPT-4 enhancement complete - Cost: ${gpt_cost.total_cost:.4f}")

        # Phase 3: Claude Implementation-Ready Polish
        logger.info("Phase 3/3: Claude creating implementation-ready PRD...")
        polish_request = self._create_refinement_request(
            original_request=request,
            previous_doc=gpt_doc,
            refinement_instructions="Final polish for implementation: (1) Ensure all user stories are testable, (2) Verify technical feasibility, (3) Add security and compliance considerations, (4) Ensure development team can start immediately, (5) Add deployment and monitoring requirements"
        )
        claude_config_dict = self.llm_factory._DEFAULT_CONFIGS[ProviderName.CLAUDE].copy()
        claude_api_key = self.llm_factory._get_api_key(ProviderName.CLAUDE)
        claude_config = LLMConfig(api_key=claude_api_key, **claude_config_dict)
        claude_strategy = ClaudeStrategy(claude_config)
        final_doc, claude_cost = await claude_strategy.generate_prd(polish_request, brd_document)
        total_cost += claude_cost.total_cost
        costs_by_provider['claude'] = claude_cost.total_cost
        logger.info(f"✓ Claude polish complete - Cost: ${claude_cost.total_cost:.4f}")

        # Combine cost metadata
        total_input_tokens = gemini_cost.input_tokens + gpt_cost.input_tokens + claude_cost.input_tokens
        total_output_tokens = gemini_cost.output_tokens + gpt_cost.output_tokens + claude_cost.output_tokens
        total_tokens = total_input_tokens + total_output_tokens

        # Calculate weighted average cost per 1K tokens
        avg_cost_per_1k_input = (total_cost / (total_tokens / 1000)) if total_tokens > 0 else 0.0
        avg_cost_per_1k_output = avg_cost_per_1k_input  # Same for combined

        # Sum generation times
        total_gen_time = gemini_cost.generation_time_ms + gpt_cost.generation_time_ms + claude_cost.generation_time_ms

        combined_cost = CostMetadata(
            provider="multi-llm",
            model_name="gemini-2.0-flash-exp + gpt-4-turbo + claude-opus-4.1",
            total_cost=total_cost,
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            cost_per_1k_input=avg_cost_per_1k_input,
            cost_per_1k_output=avg_cost_per_1k_output,
            generation_time_ms=total_gen_time,
            cached=False,
            breakdown=costs_by_provider
        )

        logger.info(f"Multi-LLM PRD generation complete - Total cost: ${total_cost:.4f}")
        return final_doc, combined_cost

    def _create_refinement_request(
        self,
        original_request: GenerationRequest,
        previous_doc: Any,
        refinement_instructions: str
    ) -> GenerationRequest:
        """
        Create a refinement request that includes the previous document.

        Args:
            original_request: Original user request
            previous_doc: Previous LLM's output document
            refinement_instructions: Specific instructions for refinement

        Returns:
            New request with previous document context
        """
        # Convert previous document to text summary
        prev_doc_summary = self._document_to_summary(previous_doc)

        # Combine with refinement instructions
        enhanced_idea = f"""PREVIOUS DRAFT:
{prev_doc_summary}

REFINEMENT INSTRUCTIONS:
{refinement_instructions}

ORIGINAL USER IDEA:
{original_request.user_idea}

Please refine and enhance the previous draft according to the refinement instructions while staying true to the original user idea."""

        return GenerationRequest(
            user_idea=enhanced_idea,
            document_type=original_request.document_type,
            complexity=original_request.complexity,
            max_cost=original_request.max_cost,
            additional_context=original_request.additional_context
        )

    def _document_to_summary(self, doc: Any) -> str:
        """Convert document to text summary for next LLM."""
        try:
            doc_dict = doc.model_dump()
            import json
            return json.dumps(doc_dict, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to serialize document: {e}")
            return str(doc)