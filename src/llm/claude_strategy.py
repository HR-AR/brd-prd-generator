"""
Claude (Anthropic) strategy implementation.
"""

import json
import logging
import asyncio
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
    Priority
)
from ..core.exceptions import (
    LLMConnectionError,
    LLMRateLimitError,
    LLMInvalidResponseError,
    LLMTimeoutError
)

logger = logging.getLogger(__name__)


class ClaudeStrategy(LLMStrategy):
    """Claude/Anthropic implementation of LLM strategy."""

    API_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"

    def __init__(self, config: LLMConfig):
        """Initialize Claude strategy."""
        super().__init__(config)
        self.headers = {
            "x-api-key": config.api_key,
            "anthropic-version": self.API_VERSION,
            "Content-Type": "application/json"
        }

    async def _call_api(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Make API call to Claude.

        Args:
            prompt: The formatted prompt
            **kwargs: Additional parameters

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
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "system": "You are an expert business analyst and product manager specializing in creating comprehensive, professional BRD and PRD documents. Always return valid JSON responses."
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

                    # Extract content - Claude returns text in content array
                    content_text = data["content"][0]["text"]

                    # Extract JSON from the response
                    # Claude might wrap JSON in markdown code blocks
                    if "```json" in content_text:
                        start = content_text.find("```json") + 7
                        end = content_text.find("```", start)
                        content_text = content_text[start:end].strip()
                    elif "```" in content_text:
                        start = content_text.find("```") + 3
                        end = content_text.find("```", start)
                        content_text = content_text[start:end].strip()

                    # Parse JSON content
                    try:
                        parsed_content = json.loads(content_text)
                    except json.JSONDecodeError as e:
                        # Try to find JSON in the text
                        import re
                        json_match = re.search(r'\{.*\}', content_text, re.DOTALL)
                        if json_match:
                            try:
                                parsed_content = json.loads(json_match.group())
                            except json.JSONDecodeError:
                                raise LLMInvalidResponseError(
                                    f"Failed to parse JSON response: {str(e)}"
                                )
                        else:
                            raise LLMInvalidResponseError(
                                f"No valid JSON found in response: {str(e)}"
                            )

                    # Add usage information
                    usage = data.get("usage", {})
                    parsed_content["usage"] = {
                        "input_tokens": usage.get("input_tokens", 0),
                        "output_tokens": usage.get("output_tokens", 0)
                    }

                    return parsed_content

        except asyncio.TimeoutError:
            raise LLMTimeoutError(
                f"Request timed out after {self.config.timeout} seconds"
            )
        except aiohttp.ClientError as e:
            raise LLMConnectionError(f"Connection error: {str(e)}")

    def _format_prompt_for_brd(self, user_idea: str) -> str:
        """Format prompt for BRD generation."""
        return f"""
You are tasked with generating a comprehensive Business Requirements Document (BRD) based on a user's idea.

User's Idea:
{user_idea}

Please generate a complete BRD with the following JSON structure. Be thorough and professional in your responses:

{{
    "document_id": "BRD-XXXXXX" (use format BRD-followed by 6 digits),
    "project_name": "Descriptive project name based on the idea",
    "version": "1.0.0",
    "created_date": "{datetime.now().isoformat()}",
    "status": "draft",
    "executive_summary": "2-3 paragraph executive summary",
    "business_context": "Detailed business context and background",
    "objectives": [
        {{
            "objective_id": "OBJ-001",
            "description": "Clear, SMART objective",
            "success_criteria": ["Measurable criterion 1", "Measurable criterion 2"],
            "business_value": "Expected business value",
            "priority": "high/medium/low"
        }}
        // Add 3-5 objectives
    ],
    "scope": {{
        "in_scope": ["Item 1", "Item 2", "Item 3"],
        "out_of_scope": ["Item 1", "Item 2"]
    }},
    "stakeholders": [
        {{
            "name": "Stakeholder title/role",
            "role": "Their role in the project",
            "interest_influence": "high/medium/low"
        }}
        // Add 3-5 key stakeholders
    ],
    "requirements": [
        {{
            "requirement_id": "BR-001",
            "category": "functional/non_functional/business/regulatory",
            "description": "Clear requirement description",
            "rationale": "Why this is needed",
            "priority": "must_have/should_have/could_have/wont_have",
            "acceptance_criteria": ["Criterion 1", "Criterion 2"]
        }}
        // Add 8-12 requirements
    ],
    "assumptions": ["Assumption 1", "Assumption 2"],
    "constraints": ["Constraint 1", "Constraint 2"],
    "risks": [
        {{
            "risk_id": "RISK-001",
            "description": "Risk description",
            "impact": "high/medium/low",
            "probability": "high/medium/low",
            "mitigation": "Mitigation strategy"
        }}
        // Add 3-5 risks
    ],
    "success_criteria": ["Overall success criterion 1", "Overall success criterion 2"],
    "timeline_milestones": [
        {{
            "milestone": "Milestone name",
            "target_date": "YYYY-MM-DD",
            "deliverables": ["Deliverable 1", "Deliverable 2"]
        }}
        // Add 3-5 milestones
    ]
}}

Important:
- Ensure all objectives follow SMART criteria
- Generate realistic, professional content
- Use appropriate business terminology
- Return ONLY valid JSON without any additional text or formatting
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

Related BRD Context:
- Project Name: {brd_document.project_name}
- BRD ID: {brd_document.document_id}
- Key Objectives: {', '.join([obj.description[:50] for obj in brd_document.objectives[:3]])}
- Number of Business Requirements: {len(brd_document.requirements)}

Ensure the PRD aligns with and expands upon these business requirements.
"""

        return f"""
You are tasked with generating a comprehensive Product Requirements Document (PRD) based on a user's idea.

User's Idea:
{user_idea}
{context}

Please generate a complete PRD with the following JSON structure:

{{
    "document_id": "PRD-XXXXXX" (use format PRD-followed by 6 digits),
    "product_name": "Product name based on the idea",
    "version": "1.0.0",
    "created_date": "{datetime.now().isoformat()}",
    "status": "draft",
    "related_brd_id": {f'"{brd_document.document_id}"' if brd_document else 'null'},
    "product_overview": "Comprehensive product overview",
    "target_audience": "Detailed target audience description",
    "user_personas": [
        {{
            "persona_id": "PERSONA-001",
            "name": "Persona Name",
            "description": "Detailed persona description",
            "goals": ["Goal 1", "Goal 2"],
            "pain_points": ["Pain point 1", "Pain point 2"],
            "technical_proficiency": "low/medium/high"
        }}
        // Add 2-3 personas
    ],
    "user_stories": [
        {{
            "story_id": "US-001",
            "persona_id": "PERSONA-001",
            "story": "As a [persona], I want to [action] so that [benefit]",
            "acceptance_criteria": ["Criterion 1", "Criterion 2"],
            "priority": "high/medium/low",
            "story_points": 5,
            "dependencies": []
        }}
        // Add 10-15 user stories
    ],
    "functional_requirements": [
        {{
            "requirement_id": "FR-001",
            "feature_name": "Feature name",
            "description": "Detailed description",
            "user_stories": ["US-001", "US-002"],
            "priority": "must_have/should_have/could_have/wont_have",
            "acceptance_criteria": ["Criterion 1", "Criterion 2"]
        }}
        // Add 8-12 functional requirements
    ],
    "non_functional_requirements": [
        {{
            "requirement_id": "NFR-001",
            "category": "performance/security/usability/reliability/scalability",
            "description": "Requirement description",
            "acceptance_criteria": ["Criterion 1"],
            "metrics": ["Metric 1"]
        }}
        // Add 5-8 non-functional requirements
    ],
    "technical_requirements": [
        {{
            "requirement_id": "TR-001",
            "category": "architecture/integration/data/infrastructure",
            "description": "Technical requirement",
            "technology_stack": ["Tech 1", "Tech 2"],
            "constraints": ["Constraint 1"]
        }}
        // Add 4-6 technical requirements
    ],
    "ui_ux_requirements": {{
        "design_principles": ["Principle 1", "Principle 2"],
        "wireframes_needed": ["Screen 1", "Screen 2"],
        "accessibility_standards": ["WCAG 2.1 Level AA"],
        "responsive_design": true,
        "platform_requirements": ["web", "ios", "android"]
    }},
    "data_requirements": {{
        "data_models": ["Model 1", "Model 2"],
        "data_sources": ["Source 1", "Source 2"],
        "data_privacy": ["GDPR compliance", "Data encryption"],
        "retention_policies": ["Policy 1"]
    }},
    "integration_requirements": [
        {{
            "system": "System name",
            "integration_type": "api/webhook/batch/realtime",
            "data_flow": "Description of data flow",
            "authentication": "Authentication method"
        }}
        // Add 2-4 integrations if applicable
    ],
    "success_metrics": [
        {{
            "metric": "Metric name",
            "target_value": "Target",
            "measurement_method": "How to measure",
            "review_frequency": "Daily/Weekly/Monthly"
        }}
        // Add 4-6 success metrics
    ],
    "release_plan": {{
        "mvp_scope": ["Feature 1", "Feature 2"],
        "phase_1": ["Feature 3", "Feature 4"],
        "phase_2": ["Feature 5", "Feature 6"],
        "future_enhancements": ["Enhancement 1"]
    }},
    "dependencies": ["Dependency 1", "Dependency 2"],
    "risks": [
        {{
            "risk_id": "RISK-001",
            "description": "Risk description",
            "impact": "high/medium/low",
            "probability": "high/medium/low",
            "mitigation": "Mitigation strategy"
        }}
        // Add 3-5 risks
    ]
}}

Important:
- Generate professional, technically accurate content
- Ensure user stories follow proper format
- All requirements must be testable and specific
- Return ONLY valid JSON without any additional text
"""

    def _parse_brd_response(self, response: Dict[str, Any]) -> BRDDocument:
        """Parse API response into BRDDocument."""
        try:
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

            # Build BRD document
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