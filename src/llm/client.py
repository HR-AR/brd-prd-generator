"""
Base LLM Strategy and client implementations.

This module provides the abstract base class for all LLM providers
and concrete implementations for OpenAI, Claude, and Gemini.
"""

import abc
import asyncio
import json
import logging
from typing import Any, Dict, Optional, Union
from datetime import datetime
import time
from functools import wraps

from pydantic import BaseModel, Field

from ..core.models import (
    BRDDocument,
    PRDDocument,
    GenerationRequest,
    GenerationResponse,
    CostMetadata,
    DocumentType,
    ComplexityLevel
)
from ..core.exceptions import (
    LLMConnectionError,
    LLMRateLimitError,
    LLMInvalidResponseError,
    LLMCostExceededError
)

logger = logging.getLogger(__name__)


class LLMConfig(BaseModel):
    """Configuration for LLM providers."""
    api_key: str
    model_name: str
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 30
    max_retries: int = 3
    base_delay: float = 1.0  # For exponential backoff

    # Cost configuration (per 1K tokens)
    cost_per_1k_input: float
    cost_per_1k_output: float

    # Rate limiting
    requests_per_minute: int = 60
    tokens_per_minute: int = 90000

    class Config:
        protected_namespaces = ()  # Allow model_name


def cost_tracker(func):
    """Decorator to track costs for LLM calls."""
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        start_time = time.time()

        try:
            # Execute the wrapped function
            result = await func(self, *args, **kwargs)

            # Calculate generation time
            generation_time_ms = (time.time() - start_time) * 1000

            # Update cost metadata if it exists
            if hasattr(result, 'cost_metadata') and result.cost_metadata:
                result.cost_metadata.generation_time_ms = generation_time_ms

            # Log cost information
            if hasattr(result, 'cost_metadata') and result.cost_metadata:
                logger.info(
                    f"LLM call completed - Provider: {result.cost_metadata.provider}, "
                    f"Model: {result.cost_metadata.model_name}, "
                    f"Cost: ${result.cost_metadata.total_cost:.4f}, "
                    f"Time: {generation_time_ms:.0f}ms"
                )

            return result

        except Exception as e:
            generation_time_ms = (time.time() - start_time) * 1000
            logger.error(
                f"LLM call failed after {generation_time_ms:.0f}ms: {str(e)}"
            )
            raise

    return wrapper


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retry logic with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return await func(self, *args, **kwargs)

                except LLMRateLimitError as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(
                            f"Rate limit hit, retrying in {delay:.1f}s "
                            f"(attempt {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"Max retries exceeded: {str(e)}")

                except (LLMConnectionError, LLMInvalidResponseError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"Connection/response error, retrying in {delay:.1f}s "
                            f"(attempt {attempt + 1}/{max_retries}): {str(e)}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"Max retries exceeded: {str(e)}")

                except Exception as e:
                    # Don't retry on unexpected errors
                    logger.error(f"Unexpected error in LLM call: {str(e)}")
                    raise

            # If we've exhausted retries, raise the last exception
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


class LLMStrategy(abc.ABC):
    """Abstract base class for LLM provider strategies."""

    def __init__(self, config: LLMConfig):
        """Initialize the LLM strategy with configuration."""
        self.config = config
        self._rate_limiter = RateLimiter(
            requests_per_minute=config.requests_per_minute,
            tokens_per_minute=config.tokens_per_minute
        )

    @abc.abstractmethod
    async def _call_api(
        self,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make the actual API call to the LLM provider.

        Args:
            prompt: The formatted prompt to send
            **kwargs: Additional provider-specific parameters

        Returns:
            Raw response from the API

        Raises:
            LLMConnectionError: If connection fails
            LLMRateLimitError: If rate limit is exceeded
            LLMInvalidResponseError: If response is invalid
        """
        pass

    @abc.abstractmethod
    def _format_prompt_for_brd(self, user_idea: str) -> str:
        """Format the prompt for BRD generation."""
        pass

    @abc.abstractmethod
    def _format_prompt_for_prd(
        self,
        user_idea: str,
        brd_document: Optional[BRDDocument] = None
    ) -> str:
        """Format the prompt for PRD generation."""
        pass

    @abc.abstractmethod
    def _parse_brd_response(self, response: Dict[str, Any]) -> BRDDocument:
        """Parse the API response into a BRD document."""
        pass

    @abc.abstractmethod
    def _parse_prd_response(self, response: Dict[str, Any]) -> PRDDocument:
        """Parse the API response into a PRD document."""
        pass

    @cost_tracker
    @retry_with_backoff()
    async def generate_brd(
        self,
        request: GenerationRequest
    ) -> tuple[BRDDocument, CostMetadata]:
        """
        Generate a BRD document from user idea.

        Args:
            request: The generation request containing user idea

        Returns:
            Tuple of (BRDDocument, CostMetadata)

        Raises:
            LLMCostExceededError: If cost would exceed max_cost
        """
        # Check rate limits
        await self._rate_limiter.acquire(estimated_tokens=len(request.user_idea) * 2)

        # Format prompt
        prompt = self._format_prompt_for_brd(request.user_idea)

        # Estimate cost (rough estimation)
        estimated_input_tokens = len(prompt) // 4  # Rough char to token ratio
        estimated_output_tokens = 2000  # Typical BRD response size
        estimated_cost = self._calculate_cost(
            estimated_input_tokens,
            estimated_output_tokens
        )

        if estimated_cost > request.max_cost:
            raise LLMCostExceededError(
                f"Estimated cost ${estimated_cost:.2f} exceeds "
                f"max cost ${request.max_cost:.2f}"
            )

        # Make API call
        response = await self._call_api(
            prompt=prompt,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature
        )

        # Parse response
        brd_document = self._parse_brd_response(response)

        # Calculate actual cost
        input_tokens = response.get('usage', {}).get('input_tokens', estimated_input_tokens)
        output_tokens = response.get('usage', {}).get('output_tokens', estimated_output_tokens)
        total_cost = self._calculate_cost(input_tokens, output_tokens)

        # Create cost metadata
        cost_metadata = CostMetadata(
            provider=self.__class__.__name__.replace('Strategy', '').lower(),
            model_name=self.config.model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_per_1k_input=self.config.cost_per_1k_input,
            cost_per_1k_output=self.config.cost_per_1k_output,
            total_cost=total_cost,
            generation_time_ms=0,  # Will be set by decorator
            cached=False
        )

        return brd_document, cost_metadata

    @cost_tracker
    @retry_with_backoff()
    async def generate_prd(
        self,
        request: GenerationRequest,
        brd_document: Optional[BRDDocument] = None
    ) -> tuple[PRDDocument, CostMetadata]:
        """
        Generate a PRD document from user idea and optional BRD.

        Args:
            request: The generation request containing user idea
            brd_document: Optional BRD document for context

        Returns:
            Tuple of (PRDDocument, CostMetadata)

        Raises:
            LLMCostExceededError: If cost would exceed max_cost
        """
        # Check rate limits
        await self._rate_limiter.acquire(
            estimated_tokens=len(request.user_idea) * 3
        )

        # Format prompt
        prompt = self._format_prompt_for_prd(request.user_idea, brd_document)

        # Estimate cost
        estimated_input_tokens = len(prompt) // 4
        estimated_output_tokens = 2500  # PRDs are typically longer
        estimated_cost = self._calculate_cost(
            estimated_input_tokens,
            estimated_output_tokens
        )

        if estimated_cost > request.max_cost:
            raise LLMCostExceededError(
                f"Estimated cost ${estimated_cost:.2f} exceeds "
                f"max cost ${request.max_cost:.2f}"
            )

        # Make API call
        response = await self._call_api(
            prompt=prompt,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature
        )

        # Parse response
        prd_document = self._parse_prd_response(response)

        # Link to BRD if provided
        if brd_document:
            prd_document.related_brd_id = brd_document.document_id

        # Calculate actual cost
        input_tokens = response.get('usage', {}).get('input_tokens', estimated_input_tokens)
        output_tokens = response.get('usage', {}).get('output_tokens', estimated_output_tokens)
        total_cost = self._calculate_cost(input_tokens, output_tokens)

        # Create cost metadata
        cost_metadata = CostMetadata(
            provider=self.__class__.__name__.replace('Strategy', '').lower(),
            model_name=self.config.model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_per_1k_input=self.config.cost_per_1k_input,
            cost_per_1k_output=self.config.cost_per_1k_output,
            total_cost=total_cost,
            generation_time_ms=0,  # Will be set by decorator
            cached=False
        )

        return prd_document, cost_metadata

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate the cost for given token counts."""
        input_cost = (input_tokens / 1000) * self.config.cost_per_1k_input
        output_cost = (output_tokens / 1000) * self.config.cost_per_1k_output
        return round(input_cost + output_cost, 4)


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, requests_per_minute: int, tokens_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute
        self._request_times: list[float] = []
        self._token_counts: list[tuple[float, int]] = []

    async def acquire(self, estimated_tokens: int = 0):
        """
        Acquire permission to make an API call.

        Args:
            estimated_tokens: Estimated tokens for this request

        Raises:
            LLMRateLimitError: If rate limit would be exceeded
        """
        current_time = time.time()

        # Clean old entries (older than 1 minute)
        self._request_times = [
            t for t in self._request_times
            if current_time - t < 60
        ]
        self._token_counts = [
            (t, c) for t, c in self._token_counts
            if current_time - t < 60
        ]

        # Check request rate limit
        if len(self._request_times) >= self.requests_per_minute:
            wait_time = 60 - (current_time - self._request_times[0])
            if wait_time > 0:
                logger.info(f"Rate limit: waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)

        # Check token rate limit
        total_tokens = sum(c for _, c in self._token_counts)
        if total_tokens + estimated_tokens > self.tokens_per_minute:
            # Find how long to wait
            tokens_to_free = (total_tokens + estimated_tokens) - self.tokens_per_minute
            tokens_freed = 0
            wait_until = current_time

            for token_time, token_count in self._token_counts:
                tokens_freed += token_count
                if tokens_freed >= tokens_to_free:
                    wait_until = token_time + 60
                    break

            wait_time = wait_until - current_time
            if wait_time > 0:
                logger.info(f"Token limit: waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)

        # Record this request
        self._request_times.append(current_time)
        if estimated_tokens > 0:
            self._token_counts.append((current_time, estimated_tokens))