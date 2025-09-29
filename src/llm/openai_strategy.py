"""
OpenAI (ChatGPT) strategy implementation.
"""

import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime
import aiohttp

from .client import LLMStrategy, LLMConfig
from ..core.models import (
    BRDDocument,
    PRDDocument,
    BusinessObjective,
    UserStory,
    TechnicalRequirement,
    ValidationStatus,
    Priority
)
from ..core.exceptions import (
    LLMConnectionError,
    LLMRateLimitError,
    LLMInvalidResponseError,
    LLMTimeoutError
)

logger = logging.getLogger(__name__)


class OpenAIStrategy(LLMStrategy):
    """OpenAI/ChatGPT implementation of LLM strategy."""

    API_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(self, config: LLMConfig):
        """Initialize OpenAI strategy."""
        super().__init__(config)
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }

    async def _call_api(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Make API call to OpenAI.

        Args:
            prompt: The formatted prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Raw API response

        Raises:
            LLMConnectionError: On connection failure
            LLMRateLimitError: On rate limit
            LLMInvalidResponseError: On invalid response
            LLMTimeoutError: On timeout
        """
        # Build request payload
        payload = {
            "model": self.config.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert business analyst and product manager. Generate structured, professional documents based on user requirements."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "response_format": {"type": "json_object"}  # Force JSON response
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.API_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:

                    # Check for rate limiting
                    if response.status == 429:
                        retry_after = response.headers.get("Retry-After", "60")
                        raise LLMRateLimitError(
                            f"Rate limit exceeded. Retry after {retry_after} seconds"
                        )

                    # Check for other errors
                    if response.status != 200:
                        error_text = await response.text()
                        raise LLMConnectionError(
                            f"API request failed with status {response.status}: {error_text}"
                        )

                    # Parse response
                    data = await response.json()

                    # Extract usage information
                    usage = data.get("usage", {})

                    # Extract content
                    content = data["choices"][0]["message"]["content"]

                    # Parse JSON content
                    try:
                        parsed_content = json.loads(content)
                    except json.JSONDecodeError as e:
                        raise LLMInvalidResponseError(
                            f"Failed to parse JSON response: {str(e)}"
                        )

                    # Add usage to parsed content
                    parsed_content["usage"] = {
                        "input_tokens": usage.get("prompt_tokens", 0),
                        "output_tokens": usage.get("completion_tokens", 0)
                    }

                    return parsed_content

        except aiohttp.ClientTimeout:
            raise LLMTimeoutError(
                f"Request timed out after {self.config.timeout} seconds"
            )
        except aiohttp.ClientError as e:
            raise LLMConnectionError(f"Connection error: {str(e)}")

    def _format_prompt_for_brd(self, user_idea: str) -> str:
        """Format prompt for BRD generation."""
        return f"""
Generate a comprehensive Business Requirements Document (BRD) based on the following idea:

{user_idea}

Return a JSON object with the following structure:
{{
    "document_id": "BRD-XXXXXX",
    "project_name": "...",
    "version": "1.0.0",
    "created_date": "ISO8601 timestamp",
    "status": "draft",
    "executive_summary": "...",
    "business_context": "...",
    "objectives": [
        {{
            "objective_id": "OBJ-001",
            "description": "...",
            "success_criteria": ["..."],
            "business_value": "...",
            "priority": "high|medium|low"
        }}
    ],
    "scope": {{
        "in_scope": ["..."],
        "out_of_scope": ["..."]
    }},
    "stakeholders": [
        {{
            "name": "...",
            "role": "...",
            "interest_influence": "high|medium|low"
        }}
    ],
    "requirements": [
        {{
            "requirement_id": "BR-001",
            "category": "functional|non_functional|business|regulatory",
            "description": "...",
            "rationale": "...",
            "priority": "must_have|should_have|could_have|wont_have",
            "acceptance_criteria": ["..."]
        }}
    ],
    "assumptions": ["..."],
    "constraints": ["..."],
    "risks": [
        {{
            "risk_id": "RISK-001",
            "description": "...",
            "impact": "high|medium|low",
            "probability": "high|medium|low",
            "mitigation": "..."
        }}
    ],
    "success_criteria": ["..."],
    "timeline_milestones": [
        {{
            "milestone": "...",
            "target_date": "ISO8601 date",
            "deliverables": ["..."]
        }}
    ]
}}

Ensure all objectives follow SMART criteria (Specific, Measurable, Achievable, Relevant, Time-bound).
Generate realistic and professional content based on the user's idea.
Use appropriate technical and business terminology.
"""

    def _format_prompt_for_prd(
        self,
        user_idea: str,
        brd_document: Optional[BRDDocument] = None
    ) -> str:
        """Format prompt for PRD generation."""

        context = ""
        if brd_document:
            context = f"""
Related BRD Information:
- Project: {brd_document.project_name}
- Objectives: {[obj.description for obj in brd_document.objectives]}
- Requirements: {len(brd_document.requirements)} business requirements defined
"""

        return f"""
Generate a comprehensive Product Requirements Document (PRD) based on the following idea:

{user_idea}
{context}

Return a JSON object with the following structure:
{{
    "document_id": "PRD-XXXXXX",
    "product_name": "...",
    "version": "1.0.0",
    "created_date": "ISO8601 timestamp",
    "status": "draft",
    "related_brd_id": {"null or BRD-XXXXXX" if not brd_document else f'"{brd_document.document_id}"'},
    "product_overview": "...",
    "target_audience": "...",
    "user_personas": [
        {{
            "persona_id": "PERSONA-001",
            "name": "...",
            "description": "...",
            "goals": ["..."],
            "pain_points": ["..."],
            "technical_proficiency": "low|medium|high"
        }}
    ],
    "user_stories": [
        {{
            "story_id": "US-001",
            "persona_id": "PERSONA-001",
            "story": "As a [persona], I want to [action] so that [benefit]",
            "acceptance_criteria": ["..."],
            "priority": "high|medium|low",
            "story_points": 1-13,
            "dependencies": []
        }}
    ],
    "functional_requirements": [
        {{
            "requirement_id": "FR-001",
            "feature_name": "...",
            "description": "...",
            "user_stories": ["US-001"],
            "priority": "must_have|should_have|could_have|wont_have",
            "acceptance_criteria": ["..."]
        }}
    ],
    "non_functional_requirements": [
        {{
            "requirement_id": "NFR-001",
            "category": "performance|security|usability|reliability|scalability",
            "description": "...",
            "acceptance_criteria": ["..."],
            "metrics": ["..."]
        }}
    ],
    "technical_requirements": [
        {{
            "requirement_id": "TR-001",
            "category": "architecture|integration|data|infrastructure",
            "description": "...",
            "technology_stack": ["..."],
            "constraints": ["..."]
        }}
    ],
    "ui_ux_requirements": {{
        "design_principles": ["..."],
        "wireframes_needed": ["..."],
        "accessibility_standards": ["..."],
        "responsive_design": true,
        "platform_requirements": ["web", "ios", "android"]
    }},
    "data_requirements": {{
        "data_models": ["..."],
        "data_sources": ["..."],
        "data_privacy": ["..."],
        "retention_policies": ["..."]
    }},
    "integration_requirements": [
        {{
            "system": "...",
            "integration_type": "api|webhook|batch|realtime",
            "data_flow": "...",
            "authentication": "..."
        }}
    ],
    "success_metrics": [
        {{
            "metric": "...",
            "target_value": "...",
            "measurement_method": "...",
            "review_frequency": "..."
        }}
    ],
    "release_plan": {{
        "mvp_scope": ["..."],
        "phase_1": ["..."],
        "phase_2": ["..."],
        "future_enhancements": ["..."]
    }},
    "dependencies": ["..."],
    "risks": [
        {{
            "risk_id": "RISK-001",
            "description": "...",
            "impact": "high|medium|low",
            "probability": "high|medium|low",
            "mitigation": "..."
        }}
    ]
}}

Generate professional, technically accurate content.
Ensure user stories follow the proper format.
All requirements should be testable and specific.
"""

    def _parse_brd_response(self, response: Dict[str, Any]) -> BRDDocument:
        """Parse API response into BRDDocument."""
        try:
            # The response should already be parsed JSON
            # Map the JSON structure to our BRDDocument model

            # Convert objectives
            objectives = []
            for obj in response.get("objectives", []):
                objectives.append(BusinessObjective(
                    objective_id=obj["objective_id"],
                    description=obj["description"],
                    success_criteria=obj["success_criteria"],
                    business_value=obj["business_value"],
                    priority=Priority(obj["priority"])
                ))

            # Ensure we have required fields with defaults if missing
            document_data = {
                "document_id": response.get("document_id", f"BRD-{datetime.now().strftime('%H%M%S')}"),
                "project_name": response["project_name"],
                "version": response.get("version", "1.0.0"),
                "created_date": response.get("created_date", datetime.now().isoformat()),
                "last_modified": response.get("last_modified", datetime.now().isoformat()),
                "status": response.get("status", "draft"),
                "executive_summary": response["executive_summary"],
                "business_context": response["business_context"],
                "objectives": objectives,
                "scope": response["scope"],
                "stakeholders": response.get("stakeholders", []),
                "requirements": response.get("requirements", []),
                "assumptions": response.get("assumptions", []),
                "constraints": response.get("constraints", []),
                "risks": response.get("risks", []),
                "success_criteria": response.get("success_criteria", []),
                "timeline_milestones": response.get("timeline_milestones", [])
            }

            return BRDDocument(**document_data)

        except (KeyError, ValueError) as e:
            raise LLMInvalidResponseError(
                f"Failed to parse BRD response: {str(e)}"
            )

    def _parse_prd_response(self, response: Dict[str, Any]) -> PRDDocument:
        """Parse API response into PRDDocument."""
        try:
            # Convert user stories
            user_stories = []
            for story in response.get("user_stories", []):
                user_stories.append(UserStory(
                    story_id=story["story_id"],
                    persona_id=story.get("persona_id"),
                    story=story["story"],
                    acceptance_criteria=story["acceptance_criteria"],
                    priority=Priority(story["priority"]),
                    story_points=story.get("story_points", 5),
                    dependencies=story.get("dependencies", [])
                ))

            # Convert technical requirements
            technical_requirements = []
            for req in response.get("technical_requirements", []):
                technical_requirements.append(TechnicalRequirement(
                    requirement_id=req["requirement_id"],
                    category=req["category"],
                    description=req["description"],
                    technology_stack=req.get("technology_stack", []),
                    constraints=req.get("constraints", [])
                ))

            # Build PRD document
            document_data = {
                "document_id": response.get("document_id", f"PRD-{datetime.now().strftime('%H%M%S')}"),
                "product_name": response["product_name"],
                "version": response.get("version", "1.0.0"),
                "created_date": response.get("created_date", datetime.now().isoformat()),
                "last_modified": response.get("last_modified", datetime.now().isoformat()),
                "status": response.get("status", "draft"),
                "related_brd_id": response.get("related_brd_id"),
                "product_overview": response["product_overview"],
                "target_audience": response["target_audience"],
                "user_personas": response.get("user_personas", []),
                "user_stories": user_stories,
                "functional_requirements": response.get("functional_requirements", []),
                "non_functional_requirements": response.get("non_functional_requirements", []),
                "technical_requirements": technical_requirements,
                "ui_ux_requirements": response.get("ui_ux_requirements", {}),
                "data_requirements": response.get("data_requirements", {}),
                "integration_requirements": response.get("integration_requirements", []),
                "success_metrics": response.get("success_metrics", []),
                "release_plan": response.get("release_plan", {}),
                "dependencies": response.get("dependencies", []),
                "risks": response.get("risks", [])
            }

            return PRDDocument(**document_data)

        except (KeyError, ValueError) as e:
            raise LLMInvalidResponseError(
                f"Failed to parse PRD response: {str(e)}"
            )