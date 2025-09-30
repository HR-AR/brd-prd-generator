"""
Prompt templates and builder for document generation.
"""

from typing import Optional, Dict, Any
from datetime import datetime


class PromptBuilder:
    """Builds prompts for BRD/PRD generation."""

    def __init__(self):
        """Initialize prompt builder with templates."""
        self.brd_template = self._get_brd_template()
        self.prd_template = self._get_prd_template()

    def build_brd_prompt(
        self,
        user_idea: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build prompt for BRD generation.

        Args:
            user_idea: User's business idea
            additional_context: Optional additional context

        Returns:
            Formatted prompt for BRD generation
        """
        context = ""
        if additional_context:
            context = f"\nAdditional Context:\n"
            for key, value in additional_context.items():
                context += f"- {key}: {value}\n"

        return self.brd_template.format(
            user_idea=user_idea,
            additional_context=context,
            timestamp=datetime.now().isoformat()
        )

    def build_prd_prompt(
        self,
        user_idea: str,
        brd_context: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build prompt for PRD generation.

        Args:
            user_idea: User's product idea
            brd_context: Optional BRD context
            additional_context: Optional additional context

        Returns:
            Formatted prompt for PRD generation
        """
        context = ""
        if brd_context:
            context += f"\nRelated BRD Context:\n{brd_context}\n"

        if additional_context:
            context += f"\nAdditional Context:\n"
            for key, value in additional_context.items():
                context += f"- {key}: {value}\n"

        return self.prd_template.format(
            user_idea=user_idea,
            additional_context=context,
            timestamp=datetime.now().isoformat()
        )

    def _get_brd_template(self) -> str:
        """Get BRD generation template."""
        return """
You are an expert business analyst creating a comprehensive Business Requirements Document (BRD).

USER'S BUSINESS IDEA:
{user_idea}
{additional_context}

GENERATION TIMESTAMP: {timestamp}

Create a professional BRD with the following structure and requirements:

1. DOCUMENT METADATA:
   - Generate a unique document_id in format "BRD-XXXXXX" (6 random digits)
   - Set version as "1.0.0"
   - Use the current timestamp for created_date

2. EXECUTIVE SUMMARY:
   - Write 2-3 paragraphs summarizing the business opportunity
   - Highlight key benefits and expected outcomes
   - Be concise but comprehensive

3. BUSINESS CONTEXT:
   - Explain the current situation and problems
   - Describe market conditions and opportunities
   - Identify competitive advantages

4. BUSINESS OBJECTIVES (CRITICAL - MUST BE SMART):
   Create 3-5 objectives that MUST follow SMART criteria:
   - SPECIFIC: Clear and unambiguous
   - MEASURABLE: Include numbers, percentages, or metrics
   - ACHIEVABLE: Realistic given constraints
   - RELEVANT: Aligned with business goals
   - TIME-BOUND: Include specific timeframes

   Each objective must have:
   - objective_id: "OBJ-XXX" format
   - description: Clear objective statement
   - success_criteria: List of 2-3 measurable criteria
   - business_value: Expected business impact
   - priority: high/medium/low

5. SCOPE:
   - in_scope: List 5-7 items explicitly included
   - out_of_scope: List 3-5 items explicitly excluded

6. STAKEHOLDERS:
   Identify 3-5 key stakeholders with:
   - name: Role/title (not personal names)
   - role: Their involvement in the project
   - interest_influence: high/medium/low

7. REQUIREMENTS:
   Create 8-12 business requirements with:
   - requirement_id: "BR-XXX" format
   - category: functional/non_functional/business/regulatory
   - description: Clear requirement statement
   - rationale: Why this is needed
   - priority: must_have/should_have/could_have/wont_have
   - acceptance_criteria: 2-3 testable criteria

8. ASSUMPTIONS:
   List 3-5 key assumptions

9. CONSTRAINTS:
   List 3-5 key constraints

10. RISKS:
    Identify 3-5 risks with:
    - risk_id: "RISK-XXX" format
    - description: Risk statement
    - impact: high/medium/low
    - probability: high/medium/low
    - mitigation: Mitigation strategy

11. SUCCESS CRITERIA:
    List 3-5 overall project success criteria

12. TIMELINE MILESTONES:
    Create 3-5 major milestones with:
    - milestone: Name
    - target_date: Realistic date
    - deliverables: List of deliverables

IMPORTANT REQUIREMENTS:
- All objectives MUST include specific metrics (numbers, percentages, timeframes)
- Avoid vague terms like "better", "improve" without quantification
- Ensure professional business language throughout
- Make content realistic and actionable
- Ensure all IDs follow the specified format

Return the complete BRD as a structured JSON document.
"""

    def _get_prd_template(self) -> str:
        """Get PRD generation template."""
        return """
You are an expert product manager creating a comprehensive Product Requirements Document (PRD).

USER'S PRODUCT IDEA:
{user_idea}
{additional_context}

GENERATION TIMESTAMP: {timestamp}

Create a professional PRD with the following structure:

1. DOCUMENT METADATA:
   - Generate unique document_id: "PRD-XXXXXX" (6 random digits)
   - Set version: "1.0.0"
   - Use current timestamp for created_date

2. PRODUCT OVERVIEW:
   - Comprehensive product vision and description
   - Key differentiators and value proposition
   - Target market and user segments

3. TARGET AUDIENCE:
   - Detailed description of primary users
   - User demographics and characteristics
   - User needs and pain points

4. USER PERSONAS:
   Create 2-3 detailed personas with:
   - persona_id: "PERSONA-XXX" format
   - name: Descriptive persona name
   - description: Detailed background
   - goals: List of 3-4 user goals
   - pain_points: List of 3-4 pain points
   - technical_proficiency: low/medium/high

5. USER STORIES:
   Create 10-15 user stories with:
   - story_id: "US-XXX" format
   - persona_id: Link to persona
   - story: "As a [type], I want [feature] so that [benefit]"
   - acceptance_criteria: 2-3 testable criteria
   - priority: high/medium/low
   - story_points: 1, 2, 3, 5, 8, or 13
   - dependencies: List any dependencies

6. FUNCTIONAL REQUIREMENTS:
   Create 8-12 functional requirements with:
   - requirement_id: "FR-XXX" format
   - feature_name: Clear feature name
   - description: Detailed description
   - user_stories: Link to related user stories
   - priority: must_have/should_have/could_have/wont_have
   - acceptance_criteria: 2-3 testable criteria

7. NON-FUNCTIONAL REQUIREMENTS:
   Create 5-8 NFRs covering:
   - requirement_id: "NFR-XXX" format
   - category: performance/security/usability/reliability/scalability
   - description: Clear requirement
   - acceptance_criteria: Measurable criteria
   - metrics: Specific metrics to track

8. TECHNICAL REQUIREMENTS:
   Create 4-6 technical requirements with:
   - requirement_id: "TR-XXX" format
   - category: architecture/integration/data/infrastructure
   - description: Technical requirement
   - technology_stack: List of technologies
   - constraints: Any constraints

9. UI/UX REQUIREMENTS:
   - design_principles: 3-5 principles
   - wireframes_needed: List of key screens
   - accessibility_standards: Standards to follow
   - responsive_design: true/false
   - platform_requirements: List platforms

10. DATA REQUIREMENTS:
    - data_models: Key data entities
    - data_sources: Data sources needed
    - data_privacy: Privacy requirements
    - retention_policies: Data retention rules

11. INTEGRATION REQUIREMENTS:
    List any external systems with:
    - system: System name
    - integration_type: api/webhook/batch/realtime
    - data_flow: How data flows
    - authentication: Auth method

12. SUCCESS METRICS:
    Create 4-6 metrics with:
    - metric: Metric name
    - target_value: Specific target
    - measurement_method: How to measure
    - review_frequency: How often to review

13. RELEASE PLAN:
    - mvp_scope: MVP features
    - phase_1: Phase 1 features
    - phase_2: Phase 2 features
    - future_enhancements: Future ideas

14. DEPENDENCIES:
    List 3-5 external dependencies

15. RISKS:
    Identify 3-5 product risks with mitigation strategies

IMPORTANT REQUIREMENTS:
- User stories MUST follow proper format
- All requirements must be testable
- Include specific metrics and targets
- Ensure technical accuracy
- Make content actionable and realistic

Return the complete PRD as a structured JSON document.
"""

    def build_improvement_prompt(
        self,
        original_document: Dict[str, Any],
        feedback: str
    ) -> str:
        """
        Build prompt for document improvement.

        Args:
            original_document: Original document
            feedback: Improvement feedback

        Returns:
            Formatted improvement prompt
        """
        doc_type = "BRD" if original_document.get("project_name") else "PRD"

        return f"""
You are an expert analyst improving an existing {doc_type} document.

ORIGINAL DOCUMENT:
{original_document}

IMPROVEMENT FEEDBACK:
{feedback}

Please revise the document addressing the feedback while:
1. Maintaining all existing IDs and structure
2. Improving the identified areas
3. Keeping what works well
4. Ensuring SMART criteria for objectives
5. Making all requirements more specific and measurable

Return the improved {doc_type} as a structured JSON document.
"""

    def build_validation_prompt(
        self,
        document: Dict[str, Any]
    ) -> str:
        """
        Build prompt for document validation.

        Args:
            document: Document to validate

        Returns:
            Formatted validation prompt
        """
        return f"""
Review the following document for quality and completeness:

{document}

Check for:
1. SMART criteria in objectives
2. Clear and testable requirements
3. Proper document structure
4. Missing sections
5. Vague or ambiguous language

Provide specific feedback on improvements needed.
"""