"""
Validates AI-generated content structure and completeness.
"""
import logging

logger = logging.getLogger(__name__)


def validate_content(content: dict, expected_questions: int) -> dict:
    """
    Validates the AI response has all required fields.
    Returns cleaned/fixed content or raises ValueError.
    """
    errors = []
    
    # Check top-level keys
    for key in ['pre_doc', 'post_doc', 'quiz']:
        if key not in content:
            errors.append(f"Missing top-level key: {key}")
    
    if errors:
        raise ValueError(f"Content validation failed: {', '.join(errors)}")
    
    # Validate pre_doc
    pre_doc = content['pre_doc']
    for field in ['title', 'learning_objectives', 'introduction', 'key_concepts']:
        if field not in pre_doc:
            logger.warning(f"pre_doc missing field: {field}")
            pre_doc.setdefault(field, [] if 'objectives' in field or 'concepts' in field else '')
    
    # Validate post_doc
    post_doc = content['post_doc']
    for field in ['title', 'lecture_summary', 'detailed_notes']:
        if field not in post_doc:
            logger.warning(f"post_doc missing field: {field}")
            post_doc.setdefault(field, [] if 'notes' in field else '')
    
    # Validate quiz
    quiz = content['quiz']
    if 'questions' not in quiz:
        raise ValueError("Quiz missing 'questions' field")
    
    questions = quiz['questions']
    actual_count = len(questions)
    
    if actual_count != expected_questions:
        logger.warning(f"Expected {expected_questions} questions, got {actual_count}")
        # Trim if too many
        if actual_count > expected_questions:
            quiz['questions'] = questions[:expected_questions]
    
    return content
