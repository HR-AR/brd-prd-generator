"""
LLM Response Fixer - Corrects common LLM response format errors
"""
import re
import json
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def fix_brd_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fix common BRD response format errors from LLMs.

    Common issues:
    - document_id format wrong (BRD-20231201 instead of BRD-123456)
    - interest_influence instead of interest_level + influence_level
    - Missing required fields at root level
    """
    fixed = response_data.copy()

    # Fix document_id format (must be BRD-XXXXXX with exactly 6 digits)
    if 'document_id' in fixed:
        doc_id = fixed['document_id']
        if isinstance(doc_id, str):
            # Extract any digits and take first 6
            digits = re.sub(r'[^0-9]', '', doc_id)
            if len(digits) >= 6:
                fixed['document_id'] = f"BRD-{digits[:6]}"
            elif len(digits) > 0:
                # Pad with zeros if needed
                fixed['document_id'] = f"BRD-{digits.zfill(6)}"
            else:
                # Generate random if no digits
                import random
                fixed['document_id'] = f"BRD-{random.randint(100000, 999999)}"

    # Fix stakeholders - split interest_influence into two fields
    if 'stakeholders' in fixed and isinstance(fixed['stakeholders'], list):
        for stakeholder in fixed['stakeholders']:
            if isinstance(stakeholder, dict):
                # If interest_influence exists, split it
                if 'interest_influence' in stakeholder:
                    level = stakeholder.pop('interest_influence', 'medium')
                    if 'interest_level' not in stakeholder:
                        stakeholder['interest_level'] = level
                    if 'influence_level' not in stakeholder:
                        stakeholder['influence_level'] = level

                # Ensure both fields exist
                if 'interest_level' not in stakeholder:
                    stakeholder['interest_level'] = 'medium'
                if 'influence_level' not in stakeholder:
                    stakeholder['influence_level'] = 'medium'

    # Fix objectives - ensure IDs are 3 digits
    if 'objectives' in fixed and isinstance(fixed['objectives'], list):
        for obj in fixed['objectives']:
            if isinstance(obj, dict) and 'objective_id' in obj:
                obj_id = obj['objective_id']
                if isinstance(obj_id, str):
                    # Extract digits
                    digits = re.sub(r'[^0-9]', '', obj_id)
                    if len(digits) >= 3:
                        obj['objective_id'] = f"OBJ-{digits[:3]}"
                    elif len(digits) > 0:
                        obj['objective_id'] = f"OBJ-{digits.zfill(3)}"
                    else:
                        import random
                        obj['objective_id'] = f"OBJ-{random.randint(100, 999):03d}"

            # Handle legacy 'id' field
            if isinstance(obj, dict) and 'id' in obj and 'objective_id' not in obj:
                obj['objective_id'] = obj.pop('id')

            # Ensure success_criteria is a list
            if isinstance(obj, dict) and 'success_criteria' in obj:
                if isinstance(obj['success_criteria'], str):
                    obj['success_criteria'] = [obj['success_criteria']]

            # Handle legacy 'kpis' field
            if isinstance(obj, dict) and 'kpis' in obj and 'kpi_metrics' not in obj:
                obj['kpi_metrics'] = obj.pop('kpis')

    # Ensure required root fields exist (extract from nested if needed or provide defaults)
    # Try common alternative field names
    field_mapping = {
        'title': ['project_name', 'name', 'document_title'],
        'problem_statement': ['problem', 'business_problem', 'challenge'],
        'success_metrics': ['metrics', 'kpis', 'success_criteria']
    }

    root_fields = ['title', 'executive_summary', 'business_context', 'problem_statement', 'success_metrics']
    for field in root_fields:
        if field not in fixed or not fixed[field]:
            # Try to extract from nested 'document' or 'brd' keys
            found = False
            for key in ['document', 'brd', 'brd_document']:
                if key in fixed and isinstance(fixed[key], dict) and field in fixed[key]:
                    fixed[field] = fixed[key][field]
                    found = True
                    break

            # Try alternative field names
            if not found and field in field_mapping:
                for alt_name in field_mapping[field]:
                    if alt_name in fixed and fixed[alt_name]:
                        fixed[field] = fixed[alt_name]
                        found = True
                        break

            # Provide sensible defaults if still missing
            if not found or field not in fixed or not fixed[field]:
                if field == 'title':
                    fixed['title'] = fixed.get('project_name', 'Untitled Project')
                elif field == 'problem_statement':
                    fixed['problem_statement'] = 'Problem statement to be defined based on business objectives.'
                elif field == 'success_metrics':
                    if not isinstance(fixed.get('success_metrics'), list):
                        fixed['success_metrics'] = ['Success metrics to be defined']

    logger.info(f"Fixed BRD response: document_id={fixed.get('document_id')}, title={fixed.get('title')}, stakeholders={len(fixed.get('stakeholders', []))}")

    return fixed


def fix_prd_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fix common PRD response format errors from LLMs.
    """
    fixed = response_data.copy()

    # Fix document_id format (must be PRD-XXXXXX with exactly 6 digits)
    if 'document_id' in fixed:
        doc_id = fixed['document_id']
        if isinstance(doc_id, str):
            digits = re.sub(r'[^0-9]', '', doc_id)
            if len(digits) >= 6:
                fixed['document_id'] = f"PRD-{digits[:6]}"
            elif len(digits) > 0:
                fixed['document_id'] = f"PRD-{digits.zfill(6)}"
            else:
                import random
                fixed['document_id'] = f"PRD-{random.randint(100000, 999999)}"

    # Fix user_stories - ensure IDs are 3 digits
    if 'user_stories' in fixed and isinstance(fixed['user_stories'], list):
        for story in fixed['user_stories']:
            if isinstance(story, dict) and 'story_id' in story:
                story_id = story['story_id']
                if isinstance(story_id, str):
                    digits = re.sub(r'[^0-9]', '', story_id)
                    if len(digits) >= 3:
                        story['story_id'] = f"US-{digits[:3]}"
                    elif len(digits) > 0:
                        story['story_id'] = f"US-{digits.zfill(3)}"
                    else:
                        import random
                        story['story_id'] = f"US-{random.randint(100, 999):03d}"

            # Handle legacy fields
            if isinstance(story, dict):
                if 'id' in story and 'story_id' not in story:
                    story['story_id'] = story.pop('id')
                if 'description' in story and 'story' not in story:
                    story['story'] = story.pop('description')
                if 'title' in story and 'story' not in story:
                    story['story'] = story.pop('title')

    # Fix technical_requirements
    if 'technical_requirements' in fixed and isinstance(fixed['technical_requirements'], list):
        for req in fixed['technical_requirements']:
            if isinstance(req, dict) and 'requirement_id' in req:
                req_id = req['requirement_id']
                if isinstance(req_id, str):
                    digits = re.sub(r'[^0-9]', '', req_id)
                    if len(digits) >= 3:
                        req['requirement_id'] = f"TR-{digits[:3]}"
                    elif len(digits) > 0:
                        req['requirement_id'] = f"TR-{digits.zfill(3)}"
                    else:
                        import random
                        req['requirement_id'] = f"TR-{random.randint(100, 999):03d}"

            # Handle legacy 'id' field
            if isinstance(req, dict) and 'id' in req and 'requirement_id' not in req:
                req['requirement_id'] = req.pop('id')

    logger.info(f"Fixed PRD response: document_id={fixed.get('document_id')}, user_stories={len(fixed.get('user_stories', []))}")

    return fixed