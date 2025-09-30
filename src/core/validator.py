"""
Document validation service with SMART criteria checking.
"""

import re
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import (
    BRDDocument,
    PRDDocument,
    ValidationResult,
    ValidationIssue,
    ValidationStatus,
    DocumentType
)

logger = logging.getLogger(__name__)


class DocumentValidator:
    """Validates BRD/PRD documents against quality criteria."""

    def __init__(self):
        """Initialize validator with rules."""
        self.smart_keywords = {
            "specific": ["specific", "exact", "precise", "defined", "clear"],
            "measurable": ["measure", "metric", "kpi", "percent", "%", "number", "count", "rate"],
            "achievable": ["achievable", "realistic", "feasible", "practical", "possible"],
            "relevant": ["relevant", "aligned", "business", "value", "goal", "objective"],
            "time_bound": ["date", "deadline", "timeline", "month", "quarter", "year", "week", "days"]
        }

    async def validate_brd(self, document: BRDDocument) -> ValidationResult:
        """
        Validate BRD document.

        Args:
            document: BRD document to validate

        Returns:
            Validation result with issues and recommendations
        """
        issues = []
        recommendations = []
        quality_score = 100.0

        # Validate objectives
        obj_issues = self._validate_objectives(document)
        issues.extend(obj_issues)
        quality_score -= len(obj_issues) * 5

        # Validate scope
        if not document.scope or not document.scope.get("in_scope"):
            issues.append(ValidationIssue(
                field="scope",
                severity=ValidationStatus.WARNING,
                message="Missing or incomplete scope definition",
                suggestion="Add clear in-scope and out-of-scope items"
            ))
            quality_score -= 10

        # Validate stakeholders
        if not document.stakeholders or len(document.stakeholders) < 2:
            issues.append(ValidationIssue(
                field="stakeholders",
                severity=ValidationStatus.WARNING,
                message="Insufficient stakeholder identification",
                suggestion="Identify at least 3 key stakeholders"
            ))
            quality_score -= 5

        # Validate requirements
        if document.requirements:
            req_issues = self._validate_requirements(document.requirements)
            issues.extend(req_issues)
            quality_score -= len(req_issues) * 3

        # Calculate word count
        word_count = self._calculate_word_count(document.model_dump())

        # Check document completeness
        completeness = self._check_completeness_brd(document)
        if completeness < 80:
            recommendations.append(
                f"Document completeness: {completeness}%. Consider adding missing sections."
            )
            quality_score -= (100 - completeness) / 5

        # Determine overall status
        if quality_score < 60:
            overall_status = ValidationStatus.FAILED
        elif quality_score < 80 or len([i for i in issues if i.severity == ValidationStatus.WARNING]) > 3:
            overall_status = ValidationStatus.WARNING
        else:
            overall_status = ValidationStatus.PASSED

        # SMART criteria check
        smart_status = self._validate_smart_criteria_status(document)

        return ValidationResult(
            document_id=document.document_id,
            document_type=DocumentType.BRD,
            overall_status=overall_status,
            quality_score=max(0, quality_score),
            smart_criteria_check=smart_status,
            completeness_check=ValidationStatus.PASSED if completeness >= 80 else ValidationStatus.WARNING,
            consistency_check=ValidationStatus.PASSED,  # Could add more checks
            word_count=word_count,
            readability_score=self._calculate_readability_score(document),
            issues=issues,
            recommendations=recommendations
        )

    async def validate_prd(self, document: PRDDocument) -> ValidationResult:
        """
        Validate PRD document.

        Args:
            document: PRD document to validate

        Returns:
            Validation result with issues and recommendations
        """
        issues = []
        recommendations = []
        quality_score = 100.0

        # Validate user stories
        if document.user_stories:
            story_issues = self._validate_user_stories(document.user_stories)
            issues.extend(story_issues)
            quality_score -= len(story_issues) * 3
        else:
            issues.append(ValidationIssue(
                field="user_stories",
                severity=ValidationStatus.FAILED,
                message="No user stories defined",
                suggestion="Add at least 5 user stories"
            ))
            quality_score -= 20

        # Validate technical requirements
        if document.technical_requirements:
            tech_issues = self._validate_technical_requirements(document.technical_requirements)
            issues.extend(tech_issues)
            quality_score -= len(tech_issues) * 3

        # Validate functional requirements
        if not document.functional_requirements or len(document.functional_requirements) < 5:
            issues.append(ValidationIssue(
                field="functional_requirements",
                severity=ValidationStatus.WARNING,
                message="Insufficient functional requirements",
                suggestion="Add more detailed functional requirements"
            ))
            quality_score -= 10

        # Calculate word count
        word_count = self._calculate_word_count(document.model_dump())

        # Check document completeness
        completeness = self._check_completeness_prd(document)
        if completeness < 80:
            recommendations.append(
                f"Document completeness: {completeness}%. Consider adding missing sections."
            )
            quality_score -= (100 - completeness) / 5

        # Check traceability to BRD
        traceability_check = None
        if document.related_brd_id:
            traceability_check = ValidationStatus.PASSED
            recommendations.append(f"PRD is linked to BRD: {document.related_brd_id}")

        # Determine overall status
        if quality_score < 60:
            overall_status = ValidationStatus.FAILED
        elif quality_score < 80:
            overall_status = ValidationStatus.WARNING
        else:
            overall_status = ValidationStatus.PASSED

        return ValidationResult(
            document_id=document.document_id,
            document_type=DocumentType.PRD,
            overall_status=overall_status,
            quality_score=max(0, quality_score),
            smart_criteria_check=ValidationStatus.PASSED,  # PRDs don't need SMART
            completeness_check=ValidationStatus.PASSED if completeness >= 80 else ValidationStatus.WARNING,
            consistency_check=ValidationStatus.PASSED,
            traceability_check=traceability_check,
            word_count=word_count,
            readability_score=self._calculate_readability_score(document),
            technical_accuracy_score=self._calculate_technical_accuracy(document),
            issues=issues,
            recommendations=recommendations
        )

    def _validate_objectives(self, document: BRDDocument) -> List[ValidationIssue]:
        """Validate business objectives for SMART criteria."""
        issues = []

        if not document.objectives:
            issues.append(ValidationIssue(
                field="objectives",
                severity=ValidationStatus.FAILED,
                message="No business objectives defined",
                suggestion="Add at least 3 SMART business objectives"
            ))
            return issues

        for i, obj in enumerate(document.objectives):
            # Check for SMART criteria in success criteria
            smart_score = self._calculate_smart_score(obj.success_criteria)

            if smart_score < 3:
                issues.append(ValidationIssue(
                    field=f"objectives[{i}].success_criteria",
                    severity=ValidationStatus.WARNING,
                    message=f"Objective '{obj.objective_id}' lacks SMART criteria",
                    suggestion="Make success criteria more Specific, Measurable, Achievable, Relevant, and Time-bound"
                ))

            # Check for vague criteria
            for criterion in obj.success_criteria:
                if self._is_vague(criterion):
                    issues.append(ValidationIssue(
                        field=f"objectives[{i}].success_criteria",
                        severity=ValidationStatus.WARNING,
                        message=f"Success criterion too vague: '{criterion[:50]}...'",
                        suggestion="Add specific metrics and targets"
                    ))

        return issues

    def _validate_requirements(self, requirements: List[Dict]) -> List[ValidationIssue]:
        """Validate requirements for clarity and completeness."""
        issues = []

        for i, req in enumerate(requirements):
            # Check for acceptance criteria
            if not req.get("acceptance_criteria"):
                issues.append(ValidationIssue(
                    field=f"requirements[{i}]",
                    severity=ValidationStatus.WARNING,
                    message=f"Requirement '{req.get('requirement_id', i)}' lacks acceptance criteria",
                    suggestion="Add clear acceptance criteria"
                ))

            # Check description length
            desc = req.get("description", "")
            if len(desc) < 20:
                issues.append(ValidationIssue(
                    field=f"requirements[{i}].description",
                    severity=ValidationStatus.WARNING,
                    message="Requirement description too brief",
                    suggestion="Provide more detailed requirement description"
                ))

        return issues

    def _validate_user_stories(self, user_stories: List) -> List[ValidationIssue]:
        """Validate user stories format and content."""
        issues = []

        for i, story in enumerate(user_stories):
            # Check story format (As a... I want... So that...)
            story_text = story.story if hasattr(story, 'story') else ""

            if not re.search(r"as a|as an", story_text, re.IGNORECASE):
                issues.append(ValidationIssue(
                    field=f"user_stories[{i}]",
                    severity=ValidationStatus.WARNING,
                    message=f"User story doesn't follow standard format",
                    suggestion="Use format: 'As a [user], I want [feature] so that [benefit]'"
                ))

            # Check acceptance criteria
            if not story.acceptance_criteria or len(story.acceptance_criteria) < 2:
                issues.append(ValidationIssue(
                    field=f"user_stories[{i}].acceptance_criteria",
                    severity=ValidationStatus.WARNING,
                    message="Insufficient acceptance criteria",
                    suggestion="Add at least 2-3 acceptance criteria"
                ))

        return issues

    def _validate_technical_requirements(self, tech_reqs: List) -> List[ValidationIssue]:
        """Validate technical requirements."""
        issues = []

        for i, req in enumerate(tech_reqs):
            # Check for technology stack
            if not req.technology_stack or len(req.technology_stack) == 0:
                issues.append(ValidationIssue(
                    field=f"technical_requirements[{i}].technology_stack",
                    severity=ValidationStatus.WARNING,
                    message="No technology stack specified",
                    suggestion="Specify required technologies"
                ))

        return issues

    def _calculate_smart_score(self, criteria: List[str]) -> int:
        """Calculate SMART score for success criteria."""
        score = 0
        combined_text = " ".join(criteria).lower()

        for category, keywords in self.smart_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                score += 1

        return score

    def _is_vague(self, text: str) -> bool:
        """Check if text is too vague."""
        vague_terms = [
            "better", "improve", "enhance", "good", "bad",
            "more", "less", "some", "many", "few"
        ]

        text_lower = text.lower()

        # Check if text is too short
        if len(text) < 10:
            return True

        # Check for vague terms without specific metrics
        has_vague = any(term in text_lower for term in vague_terms)
        has_specific = any(char.isdigit() for char in text) or "%" in text

        return has_vague and not has_specific

    def _validate_smart_criteria_status(self, document: BRDDocument) -> ValidationStatus:
        """Determine overall SMART criteria status."""
        if not document.objectives:
            return ValidationStatus.FAILED

        smart_scores = []
        for obj in document.objectives:
            score = self._calculate_smart_score(obj.success_criteria)
            smart_scores.append(score)

        avg_score = sum(smart_scores) / len(smart_scores) if smart_scores else 0

        if avg_score >= 4:
            return ValidationStatus.PASSED
        elif avg_score >= 3:
            return ValidationStatus.WARNING
        else:
            return ValidationStatus.FAILED

    def _check_completeness_brd(self, document: BRDDocument) -> float:
        """Check BRD document completeness percentage."""
        required_fields = [
            "document_id", "project_name", "executive_summary",
            "business_context", "objectives", "scope",
            "stakeholders", "requirements", "risks"
        ]

        present_fields = sum(
            1 for field in required_fields
            if getattr(document, field, None)
        )

        return (present_fields / len(required_fields)) * 100

    def _check_completeness_prd(self, document: PRDDocument) -> float:
        """Check PRD document completeness percentage."""
        required_fields = [
            "document_id", "product_name", "product_overview",
            "user_stories", "functional_requirements",
            "technical_requirements", "ui_ux_requirements"
        ]

        present_fields = sum(
            1 for field in required_fields
            if getattr(document, field, None)
        )

        return (present_fields / len(required_fields)) * 100

    def _calculate_word_count(self, document_dict: Dict) -> int:
        """Calculate total word count in document."""
        def count_words(obj):
            if isinstance(obj, str):
                return len(obj.split())
            elif isinstance(obj, dict):
                return sum(count_words(v) for v in obj.values())
            elif isinstance(obj, list):
                return sum(count_words(item) for item in obj)
            else:
                return 0

        return count_words(document_dict)

    def _calculate_readability_score(self, document) -> float:
        """
        Calculate readability score (simplified).

        In production, would use Flesch Reading Ease or similar.
        """
        # Simplified scoring based on average sentence length
        text = str(document.model_dump())
        sentences = text.split('.')
        words = text.split()

        if not sentences or not words:
            return 50.0

        avg_sentence_length = len(words) / len(sentences)

        # Simple scoring: shorter sentences = higher readability
        if avg_sentence_length < 15:
            return 90.0
        elif avg_sentence_length < 20:
            return 75.0
        elif avg_sentence_length < 25:
            return 60.0
        else:
            return 45.0

    def _calculate_technical_accuracy(self, document: PRDDocument) -> float:
        """Calculate technical accuracy score for PRD."""
        score = 100.0

        # Check for technical requirements
        if not document.technical_requirements:
            score -= 20

        # Check for architecture details
        if document.technical_requirements:
            has_architecture = any(
                'architecture' in str(req.category).lower()
                for req in document.technical_requirements
            )
            if not has_architecture:
                score -= 10

        # Check for API definitions
        if hasattr(document, 'api_endpoints') and not document.api_endpoints:
            score -= 10

        # Check for data requirements
        if not document.data_requirements:
            score -= 15

        return max(0, score)