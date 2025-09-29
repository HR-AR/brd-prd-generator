"""
PATTERN: Strategy Pattern
USE WHEN: Managing multiple interchangeable LLM providers (OpenAI, Claude, Gemini)
KEY CONCEPTS:
- Common interface for all LLM providers
- Runtime provider selection
- Encapsulation of provider-specific logic
- Cost tracking per provider
"""
# Source: https://dev.to/fayomihorace/become-a-python-design-strategist-using-the-strategy-pattern-6ad

import abc
from typing import Optional, Dict, Any
from pydantic import BaseModel

class Document(BaseModel):
    """Generated document with metadata."""
    content: str
    provider: str
    cost: float
    tokens_used: int
    generation_time_ms: float

class LLMCapabilities(BaseModel):
    """Provider capabilities for dynamic adaptation."""
    max_context_tokens: int
    supports_json_mode: bool
    supports_function_calling: bool
    cost_per_1k_tokens: float

class LLMStrategy(abc.ABC):
    """The Strategy interface declares operations common to all supported LLM providers."""

    @abc.abstractmethod
    async def generate(self, prompt: str, user_idea: str, **kwargs) -> Document:
        """Generates a document based on a prompt and user input."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_capabilities(self) -> LLMCapabilities:
        """Returns the capabilities of this LLM provider."""
        raise NotImplementedError

    @abc.abstractmethod
    async def validate_prompt_size(self, prompt: str) -> bool:
        """Checks if the prompt fits within the model's context window."""
        raise NotImplementedError