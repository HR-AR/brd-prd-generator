"""
Unit tests for core Pydantic models.

Tests validation, serialization, and business logic of BRD/PRD models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.core.models import (
    BRDDocument,
    PRDDocument,
    BusinessObjective,
    Stakeholder,
    UserStory,
    TechnicalRequirement,
    APIEndpoint,
    GenerationRequest,
    GenerationResponse,
    ValidationResult,
    ValidationIssue,
    CostMetadata,
    DocumentType,
    ComplexityLevel,
    ValidationStatus,
    Priority,
)


class TestBusinessObjective:
    """Test BusinessObjective model."""

    def test_valid_business_objective(self):
        """Test creating a valid business objective."""
        obj = BusinessObjective(
            objective_id="OBJ-001",
            description="Implement automated BRD/PRD generation to reduce creation time from weeks to minutes",
            success_criteria=[
                "Documents generated in under 2 minutes",
                "95% of documents pass quality validation",
                "Cost per document under $2.00"
            ],
            business_value="Reduce document creation time by 99% and save thousands of hours annually",
            priority=Priority.HIGH,
            kpi_metrics=["Time to document", "Quality score", "Cost per document"]
        )
        assert obj.objective_id == "OBJ-001"
        assert len(obj.success_criteria) == 3
        assert obj.priority == Priority.HIGH

    def test_invalid_success_criteria(self):
        """Test that vague success criteria are rejected."""
        with pytest.raises(ValidationError) as excinfo:
            BusinessObjective(
                objective_id="OBJ-002",
                description="Make the system better in various ways",
                success_criteria=["Better"],  # Too vague
                business_value="Improve overall system performance",
                priority=Priority.MEDIUM
            )
        assert "too vague" in str(excinfo.value).lower()


class TestBRDDocument:
    """Test BRDDocument model."""

    @pytest.fixture
    def valid_brd_data(self):
        """Provide valid BRD document data."""
        return {
            "document_id": "BRD-123456",
            "title": "BRD/PRD Generator System Requirements",
            "executive_summary": "This document outlines the business requirements for an automated system that generates Business Requirement Documents (BRD) and Product Requirement Documents (PRD) using multiple LLM providers.",
            "business_context": "Organizations spend 2-3 weeks creating requirement documents manually. This leads to inconsistent quality, delayed project starts, and high costs. An automated system can reduce this to minutes while improving quality and consistency.",
            "problem_statement": "Manual document creation is time-consuming, error-prone, and lacks consistency across teams and projects.",
            "objectives": [
                {
                    "objective_id": "OBJ-001",
                    "description": "Automate BRD/PRD generation to reduce time from weeks to minutes",
                    "success_criteria": [
                        "Document generation completed in under 2 minutes",
                        "Support for multiple document formats"
                    ],
                    "business_value": "Reduce document creation time by 99% and save thousands of hours annually",
                    "priority": "high"
                }
            ],
            "scope": {
                "in_scope": ["Document generation", "Multi-LLM support", "Quality validation"],
                "out_of_scope": ["Visual mockups", "Project management integration"]
            },
            "stakeholders": [
                {
                    "name": "Product Manager",
                    "role": "Primary User",
                    "interest_level": "high",
                    "influence_level": "high"
                }
            ],
            "success_metrics": ["Time reduction > 90%", "Quality score > 95%"]
        }

    def test_valid_brd_creation(self, valid_brd_data):
        """Test creating a valid BRD document."""
        brd = BRDDocument(**valid_brd_data)
        assert brd.document_id == "BRD-123456"
        assert len(brd.objectives) == 1
        assert "in_scope" in brd.scope

    def test_invalid_document_id_format(self, valid_brd_data):
        """Test that invalid document ID format is rejected."""
        valid_brd_data["document_id"] = "INVALID-ID"
        with pytest.raises(ValidationError) as excinfo:
            BRDDocument(**valid_brd_data)
        assert "document_id" in str(excinfo.value)

    def test_scope_validation(self, valid_brd_data):
        """Test that scope must have required sections."""
        valid_brd_data["scope"] = {"in_scope": ["Something"]}  # Missing out_of_scope
        with pytest.raises(ValidationError) as excinfo:
            BRDDocument(**valid_brd_data)
        assert "out_of_scope" in str(excinfo.value)


class TestUserStory:
    """Test UserStory model."""

    def test_valid_user_story(self):
        """Test creating a valid user story."""
        story = UserStory(
            story_id="US-001",
            persona_id="PERSONA-001",
            story="As a Product Manager, I want to generate a BRD from unstructured ideas so that I can quickly formalize requirements",
            acceptance_criteria=[
                "Input accepts unstructured text",
                "Output is properly formatted BRD",
                "Generation takes less than 45 seconds"
            ],
            priority=Priority.HIGH,
            story_points=5,
            dependencies=[]
        )
        assert "Product Manager" in story.story
        assert story.priority == Priority.HIGH

    def test_invalid_priority(self):
        """Test that invalid story points is rejected."""
        with pytest.raises(ValidationError) as excinfo:
            UserStory(
                story_id="US-001",
                persona_id="PERSONA-001",
                story="As a User, I want to do something so that it works",
                acceptance_criteria=["It works"],
                priority=Priority.LOW,
                story_points=20,  # Invalid - should be 1-13
                dependencies=[]
            )
        assert "story_points" in str(excinfo.value)


class TestPRDDocument:
    """Test PRDDocument model."""

    @pytest.fixture
    def valid_prd_data(self):
        """Provide valid PRD document data."""
        return {
            "document_id": "PRD-654321",
            "related_brd_id": "BRD-123456",
            "product_name": "BRD/PRD Generator",
            "product_vision": "Automate requirement document creation using AI to reduce time and improve quality",
            "target_audience": ["Product Managers", "Business Analysts", "Engineering Teams"],
            "value_proposition": "Reduce document creation time by 90% while ensuring consistent quality",
            "user_stories": [
                {
                    "story_id": "US-001",
                    "persona_id": "PERSONA-001",
                    "story": "As a Product Manager, I want to generate documents quickly so that I can focus on strategy",
                    "acceptance_criteria": ["Documents generated in < 2 minutes"],
                    "priority": "high",
                    "story_points": 5,
                    "dependencies": []
                }
            ],
            "features": [
                {"name": "Multi-LLM Support", "description": "Support OpenAI, Claude, and Gemini"}
            ],
            "technical_requirements": [
                {
                    "requirement_id": "TR-001",
                    "category": "performance",
                    "description": "System must generate documents in under 60 seconds",
                    "technology_stack": ["Python", "FastAPI"],
                    "constraints": ["Must handle concurrent requests"]
                }
            ],
            "technology_stack": ["Python", "FastAPI", "Pydantic"],
            "acceptance_criteria": ["All tests pass", "Performance targets met"],
            "metrics_and_kpis": ["Generation time < 60s", "Cost < $2.00"]
        }

    def test_valid_prd_creation(self, valid_prd_data):
        """Test creating a valid PRD document."""
        prd = PRDDocument(**valid_prd_data)
        assert prd.document_id == "PRD-654321"
        assert prd.related_brd_id == "BRD-123456"
        assert len(prd.user_stories) == 1

    def test_related_brd_validation(self, valid_prd_data):
        """Test that related BRD ID must follow correct format."""
        valid_prd_data["related_brd_id"] = "WRONG-FORMAT"
        with pytest.raises(ValidationError) as excinfo:
            PRDDocument(**valid_prd_data)
        assert "related_brd_id" in str(excinfo.value)


class TestGenerationRequest:
    """Test GenerationRequest model."""

    def test_valid_generation_request(self):
        """Test creating a valid generation request."""
        request = GenerationRequest(
            user_idea="I want to build a mobile app for dog walkers that helps them manage their clients, track walks, and handle payments. The app should support GPS tracking and send updates to pet owners.",
            document_type=DocumentType.BOTH,
            complexity=ComplexityLevel.MODERATE,
            max_cost=2.0
        )
        assert request.document_type == DocumentType.BOTH
        assert request.max_cost == 2.0

    def test_idea_length_validation(self):
        """Test that user idea has minimum length."""
        with pytest.raises(ValidationError) as excinfo:
            GenerationRequest(
                user_idea="Too short",
                document_type=DocumentType.BRD
            )
        assert "at least 50 characters" in str(excinfo.value).lower()

    def test_max_cost_validation(self):
        """Test that max cost has reasonable limits."""
        with pytest.raises(ValidationError) as excinfo:
            GenerationRequest(
                user_idea="A" * 100,  # Valid length
                max_cost=15.0  # Too high
            )
        assert "max_cost" in str(excinfo.value)


class TestValidationResult:
    """Test ValidationResult model."""

    def test_valid_validation_result(self):
        """Test creating a valid validation result."""
        result = ValidationResult(
            document_id="BRD-123456",
            document_type=DocumentType.BRD,
            overall_status=ValidationStatus.PASSED,
            quality_score=92.5,
            smart_criteria_check=ValidationStatus.PASSED,
            completeness_check=ValidationStatus.PASSED,
            consistency_check=ValidationStatus.WARNING,
            word_count=1500,
            readability_score=75.0,
            issues=[
                ValidationIssue(
                    field="success_criteria",
                    severity=ValidationStatus.WARNING,
                    message="Some criteria lack measurable targets",
                    suggestion="Add specific metrics to success criteria"
                )
            ],
            recommendations=["Consider adding more stakeholders"]
        )
        assert result.is_valid
        assert result.needs_review  # Due to WARNING status

    def test_quality_score_range(self):
        """Test that quality score is within valid range."""
        with pytest.raises(ValidationError) as excinfo:
            ValidationResult(
                document_id="BRD-123456",
                document_type=DocumentType.BRD,
                overall_status=ValidationStatus.PASSED,
                quality_score=150.0,  # Out of range
                smart_criteria_check=ValidationStatus.PASSED,
                completeness_check=ValidationStatus.PASSED,
                consistency_check=ValidationStatus.PASSED,
                word_count=1500,
                readability_score=75.0
            )
        assert "quality_score" in str(excinfo.value)


class TestCostMetadata:
    """Test CostMetadata model."""

    def test_valid_cost_metadata(self):
        """Test creating valid cost metadata."""
        cost = CostMetadata(
            provider="openai",
            model_name="gpt-5",
            input_tokens=1000,
            output_tokens=500,
            cost_per_1k_input=0.03,
            cost_per_1k_output=0.06,
            total_cost=0.06,
            generation_time_ms=1250.5,
            cached=False
        )
        assert cost.total_cost == 0.06
        assert cost.cost_efficiency == 25000.0  # (1000+500)/0.06

    def test_cost_efficiency_zero_cost(self):
        """Test cost efficiency when cost is zero (cached)."""
        cost = CostMetadata(
            provider="cache",
            model_name="cached",
            input_tokens=1000,
            output_tokens=500,
            cost_per_1k_input=0,
            cost_per_1k_output=0,
            total_cost=0,
            generation_time_ms=10.0,
            cached=True
        )
        assert cost.cost_efficiency == float('inf')