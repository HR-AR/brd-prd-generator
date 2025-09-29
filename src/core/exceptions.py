"""
Custom exceptions for the BRD/PRD Generator system.
"""


class BRDPRDGeneratorError(Exception):
    """Base exception for all BRD/PRD Generator errors."""
    pass


# LLM-related exceptions
class LLMError(BRDPRDGeneratorError):
    """Base exception for LLM-related errors."""
    pass


class LLMConnectionError(LLMError):
    """Raised when connection to LLM provider fails."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when LLM rate limit is exceeded."""
    pass


class LLMInvalidResponseError(LLMError):
    """Raised when LLM returns invalid or unparseable response."""
    pass


class LLMCostExceededError(LLMError):
    """Raised when estimated cost exceeds maximum allowed."""
    pass


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out."""
    pass


# Validation exceptions
class ValidationError(BRDPRDGeneratorError):
    """Base exception for validation errors."""
    pass


class DocumentValidationError(ValidationError):
    """Raised when document fails validation."""
    pass


class SMARTCriteriaError(ValidationError):
    """Raised when SMART criteria validation fails."""
    pass


# Repository exceptions
class RepositoryError(BRDPRDGeneratorError):
    """Base exception for repository errors."""
    pass


class DocumentNotFoundError(RepositoryError):
    """Raised when requested document is not found."""
    pass


class DocumentAlreadyExistsError(RepositoryError):
    """Raised when attempting to create duplicate document."""
    pass


class StorageError(RepositoryError):
    """Raised when storage operations fail."""
    pass


# Configuration exceptions
class ConfigurationError(BRDPRDGeneratorError):
    """Base exception for configuration errors."""
    pass


class MissingAPIKeyError(ConfigurationError):
    """Raised when required API key is missing."""
    pass


class InvalidConfigurationError(ConfigurationError):
    """Raised when configuration is invalid."""
    pass


# Factory exceptions
class FactoryError(BRDPRDGeneratorError):
    """Base exception for factory errors."""
    pass


class UnsupportedProviderError(FactoryError):
    """Raised when unsupported LLM provider is requested."""
    pass


class NoAvailableProviderError(FactoryError):
    """Raised when no suitable provider is available."""
    pass