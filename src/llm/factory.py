"""
LLM Factory for intelligent provider selection.

This module implements the Factory pattern to select the most appropriate
LLM provider based on task complexity, cost constraints, and availability.
"""

import logging
import os
from typing import Dict, Optional, Type
from enum import Enum

from .client import LLMStrategy, LLMConfig
from .openai_strategy import OpenAIStrategy
from .claude_strategy import ClaudeStrategy
from .gemini_strategy import GeminiStrategy
from ..core.models import ComplexityLevel, DocumentType
from ..core.exceptions import (
    UnsupportedProviderError,
    NoAvailableProviderError,
    MissingAPIKeyError,
    InvalidConfigurationError
)

logger = logging.getLogger(__name__)


class ProviderName(Enum):
    """Enum for LLM provider names."""
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"


class TaskComplexity(Enum):
    """Task complexity levels for provider selection."""
    SIMPLE = "simple"      # Basic requirements, standard format
    MODERATE = "moderate"  # Average complexity, some customization
    COMPLEX = "complex"    # High complexity, extensive requirements


class LLMFactory:
    """
    Factory for creating LLM strategy instances.

    Implements intelligent provider selection based on:
    - Task complexity
    - Cost constraints
    - Provider availability
    - Quality requirements
    """

    # Provider strategy mappings
    _PROVIDER_STRATEGIES: Dict[ProviderName, Type[LLMStrategy]] = {
        ProviderName.OPENAI: OpenAIStrategy,
        ProviderName.CLAUDE: ClaudeStrategy,
        ProviderName.GEMINI: GeminiStrategy
    }

    # Default configurations for each provider
    _DEFAULT_CONFIGS = {
        ProviderName.OPENAI: {
            "model_name": "gpt-4-turbo-preview",
            "max_tokens": 4096,
            "temperature": 0.7,
            "timeout": 60,
            "max_retries": 3,
            "base_delay": 1.0,
            "cost_per_1k_input": 0.01,    # $0.01 per 1K input tokens
            "cost_per_1k_output": 0.03,   # $0.03 per 1K output tokens
            "requests_per_minute": 500,
            "tokens_per_minute": 150000
        },
        ProviderName.CLAUDE: {
            "model_name": "claude-opus-4-1-20250805",  # Claude Opus 4.1 - Latest and most powerful (Aug 2025)
            "max_tokens": 4096,
            "temperature": 0.7,
            "timeout": 60,
            "max_retries": 3,
            "base_delay": 1.0,
            "cost_per_1k_input": 0.015,   # $15 per 1M tokens = $0.015 per 1K
            "cost_per_1k_output": 0.075,  # $75 per 1M tokens = $0.075 per 1K
            "requests_per_minute": 1000,
            "tokens_per_minute": 100000
        },
        ProviderName.GEMINI: {
            "model_name": "gemini-1.5-pro",
            "max_tokens": 8192,
            "temperature": 0.7,
            "timeout": 60,
            "max_retries": 3,
            "base_delay": 1.0,
            "cost_per_1k_input": 0.00125,  # $0.00125 per 1K input tokens
            "cost_per_1k_output": 0.005,   # $0.005 per 1K output tokens
            "requests_per_minute": 360,
            "tokens_per_minute": 1000000
        }
    }

    # Complexity to provider mapping (preference order)
    _COMPLEXITY_PROVIDER_MAP = {
        TaskComplexity.SIMPLE: ProviderName.GEMINI,     # Cheapest, good for simple tasks
        TaskComplexity.MODERATE: ProviderName.OPENAI,   # Balanced cost/quality
        TaskComplexity.COMPLEX: ProviderName.CLAUDE,    # Best quality for complex tasks
    }

    # Provider preference order for fallbacks
    _PROVIDER_PREFERENCE_ORDER = [
        ProviderName.OPENAI,   # Most reliable
        ProviderName.CLAUDE,   # High quality
        ProviderName.GEMINI,   # Cost-effective
    ]

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the LLM Factory.

        Args:
            config: Optional configuration override
        """
        self.config = config or {}
        self._available_providers = self._check_available_providers()

        if not self._available_providers:
            raise NoAvailableProviderError(
                "No LLM providers are available. Please set at least one API key "
                "(OPENAI_API_KEY, CLAUDE_API_KEY, or GEMINI_API_KEY)"
            )

        logger.info(
            f"LLM Factory initialized with available providers: "
            f"{[p.value for p in self._available_providers]}"
        )

    def _check_available_providers(self) -> list[ProviderName]:
        """Check which providers have API keys configured."""
        available = []

        # Check environment variables for API keys
        if os.getenv("OPENAI_API_KEY") or self.config.get("openai_api_key"):
            available.append(ProviderName.OPENAI)

        if os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY") or \
           self.config.get("claude_api_key") or self.config.get("anthropic_api_key"):
            available.append(ProviderName.CLAUDE)

        if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or \
           self.config.get("gemini_api_key") or self.config.get("google_api_key"):
            available.append(ProviderName.GEMINI)

        return available

    def _get_api_key(self, provider: ProviderName) -> str:
        """
        Get API key for a provider.

        Args:
            provider: The provider name

        Returns:
            API key string

        Raises:
            MissingAPIKeyError: If API key is not found
        """
        # Check config first
        if provider == ProviderName.OPENAI:
            key = self.config.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
        elif provider == ProviderName.CLAUDE:
            key = (self.config.get("claude_api_key") or
                   self.config.get("anthropic_api_key") or
                   os.getenv("CLAUDE_API_KEY") or
                   os.getenv("ANTHROPIC_API_KEY"))
        elif provider == ProviderName.GEMINI:
            key = (self.config.get("gemini_api_key") or
                   self.config.get("google_api_key") or
                   os.getenv("GEMINI_API_KEY") or
                   os.getenv("GOOGLE_API_KEY"))
        else:
            raise UnsupportedProviderError(f"Unknown provider: {provider}")

        if not key:
            raise MissingAPIKeyError(
                f"API key not found for {provider.value}. "
                f"Please set the appropriate environment variable."
            )

        return key

    def _estimate_complexity(
        self,
        user_idea: str,
        document_type: DocumentType
    ) -> TaskComplexity:
        """
        Estimate task complexity based on input.

        Args:
            user_idea: The user's idea text
            document_type: Type of document to generate

        Returns:
            Estimated task complexity
        """
        # Simple heuristic based on text length and document type
        idea_length = len(user_idea)

        # If generating both documents, it's at least moderate
        if document_type == DocumentType.BOTH:
            if idea_length > 1000:
                return TaskComplexity.COMPLEX
            else:
                return TaskComplexity.MODERATE

        # For single documents
        if idea_length < 500:
            return TaskComplexity.SIMPLE
        elif idea_length < 1500:
            return TaskComplexity.MODERATE
        else:
            return TaskComplexity.COMPLEX

    def create_strategy(
        self,
        provider: Optional[ProviderName] = None,
        complexity: Optional[ComplexityLevel] = None,
        user_idea: Optional[str] = None,
        document_type: Optional[DocumentType] = None,
        max_cost: Optional[float] = None
    ) -> LLMStrategy:
        """
        Create an LLM strategy instance.

        Args:
            provider: Specific provider to use (optional)
            complexity: Task complexity level (optional)
            user_idea: User's idea for complexity estimation (optional)
            document_type: Document type for complexity estimation (optional)
            max_cost: Maximum cost constraint (optional)

        Returns:
            Configured LLM strategy instance

        Raises:
            UnsupportedProviderError: If provider is not supported
            NoAvailableProviderError: If no suitable provider is available
            InvalidConfigurationError: If configuration is invalid
        """
        # If specific provider is requested
        if provider:
            if provider not in self._available_providers:
                raise NoAvailableProviderError(
                    f"Provider {provider.value} is not available. "
                    f"Available providers: {[p.value for p in self._available_providers]}"
                )
            selected_provider = provider

        # Otherwise, select based on complexity
        else:
            # Estimate complexity if not provided
            if complexity is None and user_idea and document_type:
                task_complexity = self._estimate_complexity(user_idea, document_type)
            elif complexity:
                # Map ComplexityLevel to TaskComplexity
                complexity_map = {
                    ComplexityLevel.SIMPLE: TaskComplexity.SIMPLE,
                    ComplexityLevel.MODERATE: TaskComplexity.MODERATE,
                    ComplexityLevel.COMPLEX: TaskComplexity.COMPLEX
                }
                task_complexity = complexity_map[complexity]
            else:
                # Default to moderate
                task_complexity = TaskComplexity.MODERATE

            # Select provider based on complexity
            selected_provider = self._select_provider_by_complexity(
                task_complexity,
                max_cost
            )

        # Create and return strategy
        return self._create_provider_strategy(selected_provider)

    def _select_provider_by_complexity(
        self,
        complexity: TaskComplexity,
        max_cost: Optional[float] = None
    ) -> ProviderName:
        """
        Select provider based on complexity and cost constraints.

        Args:
            complexity: Task complexity
            max_cost: Maximum cost constraint

        Returns:
            Selected provider name
        """
        # Get preferred provider for complexity
        preferred = self._COMPLEXITY_PROVIDER_MAP[complexity]

        # Check if preferred is available
        if preferred in self._available_providers:
            # Check cost constraint if provided
            if max_cost is not None:
                config = self._DEFAULT_CONFIGS[preferred]
                estimated_cost = self._estimate_cost_for_provider(
                    preferred,
                    complexity
                )
                if estimated_cost <= max_cost:
                    return preferred
                else:
                    # Try to find cheaper alternative
                    for provider in [ProviderName.GEMINI, ProviderName.OPENAI, ProviderName.CLAUDE]:
                        if provider in self._available_providers:
                            est_cost = self._estimate_cost_for_provider(provider, complexity)
                            if est_cost <= max_cost:
                                logger.info(
                                    f"Selected {provider.value} due to cost constraint "
                                    f"(${est_cost:.2f} <= ${max_cost:.2f})"
                                )
                                return provider
            else:
                return preferred

        # Fall back to first available provider
        for provider in self._PROVIDER_PREFERENCE_ORDER:
            if provider in self._available_providers:
                logger.warning(
                    f"Preferred provider {preferred.value} not available, "
                    f"falling back to {provider.value}"
                )
                return provider

        raise NoAvailableProviderError(
            "No suitable provider found for the given constraints"
        )

    def _estimate_cost_for_provider(
        self,
        provider: ProviderName,
        complexity: TaskComplexity
    ) -> float:
        """
        Estimate cost for a provider based on complexity.

        Args:
            provider: Provider name
            complexity: Task complexity

        Returns:
            Estimated cost in dollars
        """
        config = self._DEFAULT_CONFIGS[provider]

        # Estimate token counts based on complexity
        token_estimates = {
            TaskComplexity.SIMPLE: (1000, 2000),    # (input, output)
            TaskComplexity.MODERATE: (1500, 3000),
            TaskComplexity.COMPLEX: (2000, 4000)
        }

        input_tokens, output_tokens = token_estimates[complexity]

        # Calculate cost
        input_cost = (input_tokens / 1000) * config["cost_per_1k_input"]
        output_cost = (output_tokens / 1000) * config["cost_per_1k_output"]

        return input_cost + output_cost

    def _create_provider_strategy(self, provider: ProviderName) -> LLMStrategy:
        """
        Create a strategy instance for a provider.

        Args:
            provider: Provider name

        Returns:
            Configured strategy instance
        """
        # Get strategy class
        strategy_class = self._PROVIDER_STRATEGIES[provider]

        # Get configuration
        default_config = self._DEFAULT_CONFIGS[provider].copy()

        # Override with any custom config
        if provider.value in self.config:
            default_config.update(self.config[provider.value])

        # Get API key
        api_key = self._get_api_key(provider)

        # Create config object
        llm_config = LLMConfig(
            api_key=api_key,
            **default_config
        )

        # Create and return strategy
        strategy = strategy_class(llm_config)

        logger.info(
            f"Created {provider.value} strategy with model {llm_config.model_name}"
        )

        return strategy

    def get_available_providers(self) -> list[str]:
        """Get list of available provider names."""
        return [p.value for p in self._available_providers]

    def get_provider_info(self, provider: ProviderName) -> Dict:
        """
        Get information about a provider.

        Args:
            provider: Provider name

        Returns:
            Dictionary with provider information
        """
        if provider not in self._PROVIDER_STRATEGIES:
            raise UnsupportedProviderError(f"Unknown provider: {provider}")

        config = self._DEFAULT_CONFIGS[provider]
        available = provider in self._available_providers

        return {
            "name": provider.value,
            "available": available,
            "model": config["model_name"],
            "cost_per_1k_input": config["cost_per_1k_input"],
            "cost_per_1k_output": config["cost_per_1k_output"],
            "max_tokens": config["max_tokens"],
            "rate_limits": {
                "requests_per_minute": config["requests_per_minute"],
                "tokens_per_minute": config["tokens_per_minute"]
            }
        }


# Singleton instance
_factory_instance: Optional[LLMFactory] = None


def get_llm_factory(config: Optional[Dict] = None) -> LLMFactory:
    """
    Get or create the LLM factory singleton.

    Args:
        config: Optional configuration

    Returns:
        LLM factory instance
    """
    global _factory_instance

    if _factory_instance is None:
        _factory_instance = LLMFactory(config)

    return _factory_instance