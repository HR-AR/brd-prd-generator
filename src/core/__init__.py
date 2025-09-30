"""
Core module for BRD/PRD Generator.
"""

from .models import (
    # Enums
    DocumentType,
    ValidationStatus,
    ComplexityLevel,
    Priority,

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

# Import new modules
from .generator import DocumentGenerator
from .validator import DocumentValidator
from .prompts import PromptBuilder

__all__ = [
    # Enums
    'DocumentType',
    'ValidationStatus',
    'ComplexityLevel',
    'Priority',

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
    'NoAvailableProviderError',

    # Generator and utilities
    'DocumentGenerator',
    'DocumentValidator',
    'PromptBuilder'
]