"""
PATTERN: Factory Method Pattern
USE WHEN: Centralizing LLM client creation and intelligent provider selection
KEY CONCEPTS:
- Centralized object creation
- Runtime provider selection based on context
- Configuration and credential management
- Cost-optimized provider selection logic
"""
# Source: https://aloyan.medium.com/mastering-python-leveraging-factory-method-design-pattern-for-clean-and-scalable-code-b26aa8117847

import os
from typing import Literal, Type, Dict, Optional
from enum import Enum

from .llm_strategy_base import LLMStrategy
from .llm_strategies import OpenAIStrategy, ClaudeStrategy, GeminiStrategy

class ProviderName(str, Enum):
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"

class TaskComplexity(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"

class LLMFactory:
    """Factory for creating and selecting optimal LLM Strategy objects."""

    _STRATEGIES: Dict[ProviderName, Type[LLMStrategy]] = {
        ProviderName.OPENAI: OpenAIStrategy,
        ProviderName.CLAUDE: ClaudeStrategy,
        ProviderName.GEMINI: GeminiStrategy,
    }

    # Cost-performance matrix for intelligent selection
    _COMPLEXITY_PROVIDER_MAP = {
        TaskComplexity.SIMPLE: ProviderName.GEMINI,     # Cheapest, fastest
        TaskComplexity.MODERATE: ProviderName.OPENAI,   # Balanced
        TaskComplexity.COMPLEX: ProviderName.CLAUDE,    # Best quality
    }

    @classmethod
    def get_strategy(cls, provider: ProviderName) -> LLMStrategy:
        """
        Creates and returns an instance of a specific LLM strategy.
        Handles secure API key retrieval and validation.
        """
        strategy_class = cls._STRATEGIES.get(provider)
        if not strategy_class:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        # Centralized and secure API key handling
        api_key = cls._get_api_key(provider)
        if not api_key:
            raise ValueError(f"API key for {provider} not found in environment variables.")

        return strategy_class(api_key=api_key)

    @classmethod
    def get_optimal_strategy(
        cls,
        task_complexity: Optional[TaskComplexity] = None,
        max_cost_per_1k_tokens: Optional[float] = None,
        required_context_size: Optional[int] = None
    ) -> LLMStrategy:
        """
        Intelligently selects the best provider based on task requirements.
        Implements the cost-optimization logic required by the PRD.
        """
        # Default to moderate complexity if not specified
        if task_complexity is None:
            task_complexity = TaskComplexity.MODERATE

        # Start with complexity-based selection
        selected_provider = cls._COMPLEXITY_PROVIDER_MAP[task_complexity]

        # Override based on cost constraints
        if max_cost_per_1k_tokens is not None:
            if max_cost_per_1k_tokens < 0.025:
                selected_provider = ProviderName.GEMINI
            elif max_cost_per_1k_tokens < 0.035:
                selected_provider = ProviderName.OPENAI

        # Override based on context size requirements
        if required_context_size is not None:
            if required_context_size > 200000:
                # Only Gemini supports > 200k context
                selected_provider = ProviderName.GEMINI
            elif required_context_size > 128000:
                # Claude or Gemini
                if selected_provider == ProviderName.OPENAI:
                    selected_provider = ProviderName.CLAUDE

        print(f"Selected {selected_provider.value} for {task_complexity.value} task")
        return cls.get_strategy(selected_provider)

    @classmethod
    def _get_api_key(cls, provider: ProviderName) -> Optional[str]:
        """
        Securely retrieves API key from environment or secrets manager.
        In production, this would integrate with a proper secrets management service.
        """
        env_var_name = f"{provider.value.upper()}_API_KEY"

        # First try environment variable
        api_key = os.environ.get(env_var_name)

        # In production, fall back to secrets manager
        # if not api_key:
        #     api_key = secrets_manager.get_secret(env_var_name)

        return api_key

    @classmethod
    def get_all_capabilities(cls) -> Dict[ProviderName, dict]:
        """
        Returns capabilities of all available providers for comparison.
        Useful for UI to show provider options to users.
        """
        capabilities = {}
        for provider in ProviderName:
            try:
                # Use dummy API key for capability checking
                os.environ[f"{provider.value.upper()}_API_KEY"] = "dummy"
                strategy = cls.get_strategy(provider)
                capabilities[provider] = strategy.get_capabilities().model_dump()
            except Exception as e:
                capabilities[provider] = {"error": str(e)}
            finally:
                # Clean up dummy key
                os.environ.pop(f"{provider.value.upper()}_API_KEY", None)

        return capabilities