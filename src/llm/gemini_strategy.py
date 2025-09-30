"""
Google Gemini strategy implementation.
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


class GeminiStrategy(LLMStrategy):
    """Google Gemini implementation of LLM strategy."""

    API_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def __init__(self, config: LLMConfig):
        """Initialize Gemini strategy."""
        super().__init__(config)
        self.api_url = self.API_URL_TEMPLATE.format(model=config.model_name)

    async def _call_api(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Make API call to Gemini.

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
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "maxOutputTokens": kwargs.get("max_tokens", self.config.max_tokens),
                "responseMimeType": "application/json"  # Force JSON response
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
        }

        # Add API key to URL
        url = f"{self.api_url}?key={self.config.api_key}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
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

                    # Extract content from Gemini's response structure
                    try:
                        content_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    except (KeyError, IndexError) as e:
                        raise LLMInvalidResponseError(
                            f"Unexpected response structure: {str(e)}"
                        )

                    # Parse JSON content
                    try:
                        parsed_content = json.loads(content_text)
                    except json.JSONDecodeError as e:
                        # Try to extract JSON if wrapped in markdown
                        if "```json" in content_text:
                            start = content_text.find("```json") + 7
                            end = content_text.find("```", start)
                            content_text = content_text[start:end].strip()
                        elif "```" in content_text:
                            start = content_text.find("```") + 3
                            end = content_text.find("```", start)
                            content_text = content_text[start:end].strip()

                        try:
                            parsed_content = json.loads(content_text)
                        except json.JSONDecodeError:
                            raise LLMInvalidResponseError(
                                f"Failed to parse JSON response: {str(e)}"
                            )

                    # Add usage information (Gemini provides token counts differently)
                    usage_metadata = data.get("usageMetadata", {})
                    parsed_content["usage"] = {
                        "input_tokens": usage_metadata.get("promptTokenCount", 0),
                        "output_tokens": usage_metadata.get("candidatesTokenCount", 0)
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
You are an expert business analyst creating a Business Requirements Document (BRD).

User's Business Idea:
{user_idea}

Generate a comprehensive BRD as a JSON object with this exact structure:

{{
    "document_id": "BRD-" followed by 6 random digits,
    "project_name": "A descriptive project name",
    "version": "1.0.0",
    "created_date": "{datetime.now().isoformat()}",
    "status": "draft",
    "executive_summary": "A 2-3 paragraph executive summary of the project",
    "business_context": "Detailed business context explaining why this project is needed",
    "objectives": [
        {{
            "objective_id": "OBJ-001",
            "description": "A SMART objective (Specific, Measurable, Achievable, Relevant, Time-bound)",
            "success_criteria": ["Specific measurable criterion", "Another measurable criterion"],
            "business_value": "The business value this objective delivers",
            "priority": "high" // or "medium" or "low"
        }}
        // Include 3-5 objectives total
    ],
    "scope": {{
        "in_scope": ["What is included", "Another included item", "Third included item"],
        "out_of_scope": ["What is not included", "Another excluded item"]
    }},
    "stakeholders": [
        {{
            "name": "Stakeholder role/title",
            "role": "Their role in the project",
            "interest_influence": "high" // or "medium" or "low"
        }}
        // Include 3-5 stakeholders
    ],
    "requirements": [
        {{
            "requirement_id": "BR-001",
            "category": "functional", // or "non_functional", "business", "regulatory"
            "description": "Clear requirement description",
            "rationale": "Why this requirement is needed",
            "priority": "must_have", // or "should_have", "could_have", "wont_have"
            "acceptance_criteria": ["How to verify this requirement", "Another verification criterion"]
        }}
        // Include 8-12 requirements
    ],
    "assumptions": ["Key assumption 1", "Key assumption 2", "Key assumption 3"],
    "constraints": ["Key constraint 1", "Key constraint 2"],
    "risks": [
        {{
            "risk_id": "RISK-001",
            "description": "Description of the risk",
            "impact": "high", // or "medium" or "low"
            "probability": "medium", // or "high" or "low"
            "mitigation": "How to mitigate this risk"
        }}
        // Include 3-5 risks
    ],
    "success_criteria": ["Overall project success criterion 1", "Overall project success criterion 2"],
    "timeline_milestones": [
        {{
            "milestone": "Milestone name",
            "target_date": "2024-MM-DD",
            "deliverables": ["Deliverable 1", "Deliverable 2"]
        }}
        // Include 3-5 milestones
    ]
}}

Generate realistic, professional content based on the user's idea.
Ensure all content is relevant and properly structured.
Return ONLY the JSON object, no additional text.
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
This PRD should align with the following BRD:
- BRD ID: {brd_document.document_id}
- Project: {brd_document.project_name}
- Key Objectives: {', '.join([obj.description[:50] + '...' for obj in brd_document.objectives[:3]])}
"""

        return f"""
You are an expert product manager creating a Product Requirements Document (PRD).

User's Product Idea:
{user_idea}
{context}

Generate a comprehensive PRD as a JSON object with this exact structure:

{{
    "document_id": "PRD-" followed by 6 random digits,
    "product_name": "A descriptive product name",
    "version": "1.0.0",
    "created_date": "{datetime.now().isoformat()}",
    "status": "draft",
    "related_brd_id": {f'"{brd_document.document_id}"' if brd_document else 'null'},
    "product_overview": "Comprehensive overview of the product",
    "target_audience": "Detailed description of the target audience",
    "user_personas": [
        {{
            "persona_id": "PERSONA-001",
            "name": "Persona Name (e.g., 'Tech-Savvy Professional')",
            "description": "Detailed description of this persona",
            "goals": ["What they want to achieve", "Another goal"],
            "pain_points": ["Current frustration", "Another pain point"],
            "technical_proficiency": "medium" // or "low" or "high"
        }}
        // Include 2-3 personas
    ],
    "user_stories": [
        {{
            "story_id": "US-001",
            "persona_id": "PERSONA-001",
            "story": "As a [persona type], I want to [do something] so that [benefit]",
            "acceptance_criteria": ["When this is true", "And this is true"],
            "priority": "high", // or "medium" or "low"
            "story_points": 5, // 1, 2, 3, 5, 8, or 13
            "dependencies": []
        }}
        // Include 10-15 user stories
    ],
    "functional_requirements": [
        {{
            "requirement_id": "FR-001",
            "feature_name": "Feature Name",
            "description": "What this feature does",
            "user_stories": ["US-001", "US-002"],
            "priority": "must_have", // or "should_have", "could_have", "wont_have"
            "acceptance_criteria": ["How to verify", "Another criterion"]
        }}
        // Include 8-12 functional requirements
    ],
    "non_functional_requirements": [
        {{
            "requirement_id": "NFR-001",
            "category": "performance", // or "security", "usability", "reliability", "scalability"
            "description": "The requirement",
            "acceptance_criteria": ["How to verify"],
            "metrics": ["Specific metric"]
        }}
        // Include 5-8 non-functional requirements
    ],
    "technical_requirements": [
        {{
            "requirement_id": "TR-001",
            "category": "architecture", // or "integration", "data", "infrastructure"
            "description": "Technical requirement description",
            "technology_stack": ["Technology 1", "Technology 2"],
            "constraints": ["Constraint if any"]
        }}
        // Include 4-6 technical requirements
    ],
    "ui_ux_requirements": {{
        "design_principles": ["Principle 1", "Principle 2", "Principle 3"],
        "wireframes_needed": ["Login screen", "Dashboard", "Settings"],
        "accessibility_standards": ["WCAG 2.1 Level AA"],
        "responsive_design": true,
        "platform_requirements": ["web", "ios", "android"]
    }},
    "data_requirements": {{
        "data_models": ["User model", "Transaction model"],
        "data_sources": ["Internal database", "Third-party API"],
        "data_privacy": ["GDPR compliance", "Data encryption at rest"],
        "retention_policies": ["User data retained for 7 years"]
    }},
    "integration_requirements": [
        {{
            "system": "External System Name",
            "integration_type": "api", // or "webhook", "batch", "realtime"
            "data_flow": "Description of how data flows",
            "authentication": "OAuth 2.0" // or other method
        }}
        // Include if applicable
    ],
    "success_metrics": [
        {{
            "metric": "Metric name",
            "target_value": "Specific target",
            "measurement_method": "How to measure",
            "review_frequency": "Monthly" // or "Daily", "Weekly", "Quarterly"
        }}
        // Include 4-6 metrics
    ],
    "release_plan": {{
        "mvp_scope": ["Core feature 1", "Core feature 2"],
        "phase_1": ["Additional feature 1", "Additional feature 2"],
        "phase_2": ["Enhancement 1", "Enhancement 2"],
        "future_enhancements": ["Future idea 1"]
    }},
    "dependencies": ["External dependency 1", "External dependency 2"],
    "risks": [
        {{
            "risk_id": "RISK-001",
            "description": "Risk description",
            "impact": "high", // or "medium" or "low"
            "probability": "low", // or "medium" or "high"
            "mitigation": "How to mitigate"
        }}
        // Include 3-5 risks
    ]
}}

Generate realistic, detailed, professional content.
Ensure all user stories follow the proper format.
Return ONLY the JSON object, no additional text.
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