"""
LLM integration module for BRD/PRD Generator.
"""

from .client import (
    LLMConfig,
    LLMStrategy,
    RateLimiter,
    cost_tracker,
    retry_with_backoff
)

from .openai_strategy import OpenAIStrategy
from .claude_strategy import ClaudeStrategy
from .gemini_strategy import GeminiStrategy

from .factory import (
    LLMFactory,
    ProviderName,
    TaskComplexity,
    get_llm_factory
)

__all__ = [
    # Client classes
    'LLMConfig',
    'LLMStrategy',
    'RateLimiter',

    # Decorators
    'cost_tracker',
    'retry_with_backoff',

    # Strategy implementations
    'OpenAIStrategy',
    'ClaudeStrategy',
    'GeminiStrategy',

    # Factory
    'LLMFactory',
    'ProviderName',
    'TaskComplexity',
    'get_llm_factory'
]