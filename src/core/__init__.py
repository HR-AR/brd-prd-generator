"""
Core module for BRD/PRD Generator.
"""

from .models import (
    # Enums
    DocumentType,
    DocumentStatus,
    Priority,
    ValidationStatus,
    ComplexityLevel,

    # Core Models
    BusinessObjective,
    BRDDocument,
    UserStory,
    TechnicalRequirement,
    PRDDocument,

    # Request/Response Models
    GenerationRequest,
    GenerationResponse,

    # Validation Models
    ValidationIssue,
    ValidationResult,

    # Cost Models
    CostMetadata
)

from .exceptions import (
    # Base exceptions
    BRDPRDGeneratorError,

    # LLM exceptions
    LLMError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMInvalidResponseError,
    LLMCostExceededError,
    LLMTimeoutError,

    # Validation exceptions
    ValidationError,
    DocumentValidationError,
    SMARTCriteriaError,

    # Repository exceptions
    RepositoryError,
    DocumentNotFoundError,
    DocumentAlreadyExistsError,
    StorageError,

    # Configuration exceptions
    ConfigurationError,
    MissingAPIKeyError,
    InvalidConfigurationError,

    # Factory exceptions
    FactoryError,
    UnsupportedProviderError,
    NoAvailableProviderError
)

__all__ = [
    # Enums
    'DocumentType',
    'DocumentStatus',
    'Priority',
    'ValidationStatus',
    'ComplexityLevel',

    # Core Models
    'BusinessObjective',
    'BRDDocument',
    'UserStory',
    'TechnicalRequirement',
    'PRDDocument',

    # Request/Response Models
    'GenerationRequest',
    'GenerationResponse',

    # Validation Models
    'ValidationIssue',
    'ValidationResult',

    # Cost Models
    'CostMetadata',

    # Exceptions
    'BRDPRDGeneratorError',
    'LLMError',
    'LLMConnectionError',
    'LLMRateLimitError',
    'LLMInvalidResponseError',
    'LLMCostExceededError',
    'LLMTimeoutError',
    'ValidationError',
    'DocumentValidationError',
    'SMARTCriteriaError',
    'RepositoryError',
    'DocumentNotFoundError',
    'DocumentAlreadyExistsError',
    'StorageError',
    'ConfigurationError',
    'MissingAPIKeyError',
    'InvalidConfigurationError',
    'FactoryError',
    'UnsupportedProviderError',
    'NoAvailableProviderError'
]