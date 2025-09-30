"""
Core Pydantic models for BRD/PRD document generation system.

This module defines the data models for Business Requirement Documents (BRD),
Product Requirement Documents (PRD), and related validation/request models.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


class DocumentType(str, Enum):
    """Types of documents that can be generated."""
    BRD = "brd"
    PRD = "prd"
    BOTH = "both"


class ComplexityLevel(str, Enum):
    """Task complexity levels for intelligent LLM selection."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class ValidationStatus(str, Enum):
    """Validation status for quality checks."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class Priority(str, Enum):
    """Priority levels for objectives and requirements."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================================
# BRD Models
# ============================================================================

class BusinessObjective(BaseModel):
    """A single business objective with SMART criteria."""
    objective_id: str = Field(..., pattern="^OBJ-\\d{3}$")
    description: str = Field(..., min_length=20)
    success_criteria: List[str] = Field(..., min_length=1)
    business_value: str = Field(..., min_length=10)
    priority: Priority
    kpi_metrics: Optional[List[str]] = Field(default=None)

    @field_validator("success_criteria")
    @classmethod
    def validate_smart_criteria(cls, v: List[str]) -> List[str]:
        """Ensure success criteria follow SMART principles."""
        if len(v) < 1:
            raise ValueError("At least one success criterion is required")
        for criterion in v:
            if len(criterion) < 10:
                raise ValueError(f"Success criterion too vague: {criterion}")
        return v


class Stakeholder(BaseModel):
    """Stakeholder information."""
    name: str
    role: str
    interest_level: str = Field(..., pattern="^(high|medium|low)$")
    influence_level: str = Field(..., pattern="^(high|medium|low)$")


class BRDDocument(BaseModel):
    """Business Requirement Document model."""
    model_config = ConfigDict(validate_assignment=True)

    # Metadata
    document_id: str = Field(..., pattern="^BRD-[0-9]{6}$")
    version: str = Field(default="1.0.0", pattern="^[0-9]+\\.[0-9]+\\.[0-9]+$")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    # Core Content
    title: str = Field(..., min_length=10, max_length=200)
    executive_summary: str = Field(..., min_length=100, max_length=2000)
    business_context: str = Field(..., min_length=200)
    problem_statement: str = Field(..., min_length=100)

    # Business Requirements
    objectives: List[BusinessObjective] = Field(..., min_length=1)
    scope: Dict[str, List[str]] = Field(...)  # in_scope, out_of_scope
    constraints: Optional[List[str]] = None
    assumptions: Optional[List[str]] = None
    risks: Optional[List[Dict[str, str]]] = None  # risk, impact, mitigation

    # Stakeholders
    stakeholders: List[Stakeholder] = Field(..., min_length=1)

    # Success Metrics
    success_metrics: List[str] = Field(..., min_length=1)
    timeline: Optional[Dict[str, Any]] = None

    @field_validator("scope")
    @classmethod
    def validate_scope(cls, v: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Ensure scope has required sections."""
        required_keys = {"in_scope", "out_of_scope"}
        if not required_keys.issubset(v.keys()):
            raise ValueError(f"Scope must contain: {required_keys}")
        return v


# ============================================================================
# PRD Models
# ============================================================================

class UserStory(BaseModel):
    """User story following standard format."""
    story_id: str = Field(..., pattern="^US-\\d{3}$")
    persona_id: Optional[str] = Field(None, pattern="^PERSONA-\\d{3}$")
    story: str = Field(..., min_length=20)
    acceptance_criteria: List[str] = Field(..., min_length=1)
    priority: Priority
    story_points: int = Field(..., ge=1, le=13)
    dependencies: List[str] = Field(default_factory=list)


class TechnicalRequirement(BaseModel):
    """Technical requirement specification."""
    requirement_id: str = Field(..., pattern="^TR-\\d{3}$")
    category: str  # architecture, integration, data, infrastructure
    description: str = Field(..., min_length=20)
    technology_stack: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)


class APIEndpoint(BaseModel):
    """API endpoint specification."""
    method: str = Field(..., pattern="^(GET|POST|PUT|DELETE|PATCH)$")
    path: str = Field(..., pattern="^/[a-z0-9-/{}]+$")
    description: str
    request_body: Optional[Dict[str, Any]] = None
    response_schema: Dict[str, Any]
    error_codes: List[Dict[str, str]]


class PRDDocument(BaseModel):
    """Product Requirement Document model."""
    model_config = ConfigDict(validate_assignment=True)

    # Metadata
    document_id: str = Field(..., pattern="^PRD-[0-9]{6}$")
    version: str = Field(default="1.0.0", pattern="^[0-9]+\\.[0-9]+\\.[0-9]+$")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    related_brd_id: Optional[str] = Field(default=None, pattern="^BRD-[0-9]{6}$")

    # Product Overview
    product_name: str = Field(..., min_length=3, max_length=100)
    product_vision: str = Field(..., min_length=50, max_length=500)
    target_audience: List[str] = Field(..., min_length=1)
    value_proposition: str = Field(..., min_length=50)

    # Functional Requirements
    user_stories: List[UserStory] = Field(..., min_length=1)
    features: List[Dict[str, Any]] = Field(..., min_length=1)

    # Technical Requirements
    technical_requirements: List[TechnicalRequirement]
    architecture_overview: Optional[str] = None
    api_specifications: Optional[List[APIEndpoint]] = None
    data_model: Optional[Dict[str, Any]] = None

    # Non-Functional Requirements
    performance_requirements: Optional[List[str]] = None
    security_requirements: Optional[List[str]] = None
    compliance_requirements: Optional[List[str]] = None

    # Implementation Details
    technology_stack: List[str] = Field(..., min_length=1)
    dependencies: Optional[List[str]] = None
    deployment_requirements: Optional[Dict[str, Any]] = None

    # Success Criteria
    acceptance_criteria: List[str] = Field(..., min_length=1)
    metrics_and_kpis: List[str] = Field(..., min_length=1)

    # Release Planning
    release_plan: Optional[Dict[str, Any]] = None
    rollback_plan: Optional[str] = None


# ============================================================================
# Request/Response Models
# ============================================================================

class GenerationRequest(BaseModel):
    """Request model for document generation."""
    user_idea: str = Field(..., min_length=50, max_length=10000)
    document_type: DocumentType = DocumentType.BOTH
    complexity: ComplexityLevel = ComplexityLevel.MODERATE
    max_cost: float = Field(default=2.0, gt=0, le=10.0)
    include_examples: bool = True
    language: str = Field(default="en", pattern="^[a-z]{2}$")
    custom_requirements: Optional[Dict[str, Any]] = None
    additional_context: Optional[Dict[str, Any]] = None


class GenerationResponse(BaseModel):
    """Response model for document generation."""
    request_id: str
    status: str = Field(..., pattern="^(pending|processing|completed|failed)$")
    brd_document: Optional[BRDDocument] = None
    prd_document: Optional[PRDDocument] = None
    generation_metadata: Dict[str, Any]
    cost_breakdown: Dict[str, float]
    validation_results: Optional["ValidationResult"] = None
    error_message: Optional[str] = None


# ============================================================================
# Validation Models
# ============================================================================

class ValidationIssue(BaseModel):
    """A single validation issue found in a document."""
    field: str
    severity: ValidationStatus
    message: str
    suggestion: Optional[str] = None


class ValidationResult(BaseModel):
    """Result of document validation checks."""
    document_id: str
    document_type: DocumentType
    overall_status: ValidationStatus
    quality_score: float = Field(..., ge=0.0, le=100.0)
    issues: List[ValidationIssue] = Field(default_factory=list)

    # Specific validation checks
    smart_criteria_check: ValidationStatus
    completeness_check: ValidationStatus
    consistency_check: ValidationStatus
    traceability_check: Optional[ValidationStatus] = None  # For PRD->BRD

    # Metrics
    word_count: int
    readability_score: float
    technical_accuracy_score: Optional[float] = None

    # Recommendations
    recommendations: List[str] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Check if document passed all critical validations."""
        return self.overall_status != ValidationStatus.FAILED

    @property
    def needs_review(self) -> bool:
        """Check if document needs human review."""
        # Check if any validation check has WARNING status
        has_warning = any([
            self.overall_status == ValidationStatus.WARNING,
            self.smart_criteria_check == ValidationStatus.WARNING,
            self.completeness_check == ValidationStatus.WARNING,
            self.consistency_check == ValidationStatus.WARNING,
            self.traceability_check == ValidationStatus.WARNING if self.traceability_check else False
        ])
        return has_warning or self.quality_score < 80.0


# ============================================================================
# Cost Tracking Models
# ============================================================================

class CostMetadata(BaseModel):
    """Metadata for tracking generation costs."""
    provider: str
    model_name: str
    input_tokens: int
    output_tokens: int
    cost_per_1k_input: float
    cost_per_1k_output: float
    total_cost: float
    generation_time_ms: float
    cached: bool = False

    @property
    def cost_efficiency(self) -> float:
        """Calculate cost efficiency (tokens per dollar)."""
        if self.total_cost == 0:
            return float('inf')
        return (self.input_tokens + self.output_tokens) / self.total_cost


# Update forward reference
GenerationResponse.model_rebuild()