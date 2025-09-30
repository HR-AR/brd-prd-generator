"""
Google Gemini strategy implementation.
"""

import json
import logging
import asyncio
from typing import Any, Dict, Optional
from datetime import datetime
import aiohttp

from .response_fixer import fix_brd_response, fix_prd_response
from .prompt_templates import get_brd_prompt, get_prd_prompt
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
        return get_brd_prompt(user_idea)

    def _format_prompt_for_prd(
        self,
        user_idea: str,
        brd_document: Optional[BRDDocument] = None
    ) -> str:
        """Format prompt for PRD generation."""
        brd_id = brd_document.document_id if brd_document else None
        return get_prd_prompt(user_idea, brd_id)

    def _parse_brd_response(self, response: Dict[str, Any]) -> BRDDocument:
        """Parse API response into BRDDocument."""
        try:
            # Fix common LLM response format errors
            response = fix_brd_response(response)

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

            # Build document data matching BRDDocument model
            document_data = {
                "document_id": response.get("document_id", f"BRD-{datetime.now().strftime('%H%M%S')}"),
                "version": response.get("version", "1.0.0"),
                "title": response.get("title", "Untitled Project"),
                "executive_summary": response.get("executive_summary", ""),
                "business_context": response.get("business_context", ""),
                "problem_statement": response.get("problem_statement", ""),
                "objectives": objectives,
                "scope": response.get("scope", {"in_scope": [], "out_of_scope": []}),
                "stakeholders": response.get("stakeholders", []),
                "success_metrics": response.get("success_metrics", []),
                "constraints": response.get("constraints"),
                "assumptions": response.get("assumptions"),
                "risks": response.get("risks"),
                "timeline": response.get("timeline")
            }

            return BRDDocument(**document_data)

        except (KeyError, ValueError) as e:
            raise LLMInvalidResponseError(
                f"Failed to parse BRD response: {str(e)}"
            )

    def _parse_prd_response(self, response: Dict[str, Any]) -> PRDDocument:
        """Parse API response into PRDDocument."""
        try:
            # Fix common LLM response format errors
            response = fix_prd_response(response)

            # Convert user stories
            user_stories = []
            for story in response.get("user_stories", []):
                user_stories.append(UserStory(
                    story_id=story["story_id"],
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

            # Build PRD document matching PRDDocument model
            document_data = {
                "document_id": response.get("document_id", f"PRD-{datetime.now().strftime('%H%M%S')}"),
                "version": response.get("version", "1.0.0"),
                "related_brd_id": response.get("related_brd_id"),
                "product_name": response.get("product_name", ""),
                "product_vision": response.get("product_vision", ""),
                "target_audience": response.get("target_audience", []),
                "value_proposition": response.get("value_proposition", ""),
                "user_stories": user_stories,
                "features": response.get("features", []),
                "technical_requirements": technical_requirements,
                "technology_stack": response.get("technology_stack", []),
                "acceptance_criteria": response.get("acceptance_criteria", []),
                "metrics_and_kpis": response.get("metrics_and_kpis", []),
                "architecture_overview": response.get("architecture_overview"),
                "performance_requirements": response.get("performance_requirements"),
                "security_requirements": response.get("security_requirements"),
                "compliance_requirements": response.get("compliance_requirements"),
                "dependencies": response.get("dependencies"),
                "deployment_requirements": response.get("deployment_requirements"),
                "data_model": response.get("data_model"),
                "api_specifications": response.get("api_specifications")
            }

            return PRDDocument(**document_data)

        except (KeyError, ValueError) as e:
            raise LLMInvalidResponseError(
                f"Failed to parse PRD response: {str(e)}"
            )