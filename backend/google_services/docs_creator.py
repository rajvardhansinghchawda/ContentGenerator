"""
Creates and formats Google Docs for pre-doc and post-doc content.
"""
import logging

logger = logging.getLogger(__name__)


def create_pre_doc(docs_service, drive_service, pre_doc_data: dict, topic: str) -> tuple:
    """
    Creates a Google Doc for the pre-lecture notes.
    Returns (doc_id, doc_url).
    """
    title = pre_doc_data.get('title', f'Pre-Lecture Notes: {topic}')
    
    # Create blank doc
    doc = docs_service.documents().create(body={'title': title}).execute()
    doc_id = doc['documentId']
    
    # Build content string
    content_parts = []
    content_parts.append(f"{title}\n\n")
    
    content_parts.append("🎯 Learning Objectives\n")
    for obj in pre_doc_data.get('learning_objectives', []):
        content_parts.append(f"• {obj}\n")
    content_parts.append("\n")
    
    content_parts.append("📚 Prerequisite Knowledge\n")
    for prereq in pre_doc_data.get('prerequisite_topics', []):
        content_parts.append(f"• {prereq}\n")
    content_parts.append("\n")
    
    content_parts.append("📖 Introduction\n")
    content_parts.append(pre_doc_data.get('introduction', '') + "\n\n")
    
    content_parts.append("🔑 Key Concepts\n")
    for kc in pre_doc_data.get('key_concepts', []):
        content_parts.append(f"• {kc.get('concept', '')}: {kc.get('brief_explanation', '')}\n")
    content_parts.append("\n")
    
    content_parts.append("📋 Pre-Reading Material\n")
    content_parts.append(pre_doc_data.get('pre_reading_material', '') + "\n\n")
    
    content_parts.append("✅ Expected Outcomes\n")
    for outcome in pre_doc_data.get('expected_outcomes', []):
        content_parts.append(f"• {outcome}\n")
    
    full_text = "".join(content_parts)
    
    # Insert all text at once
    requests = [
        {'insertText': {'location': {'index': 1}, 'text': full_text}}
    ]
    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
    
    # Set sharing
    drive_service.permissions().create(
        fileId=doc_id,
        body={'role': 'reader', 'type': 'anyone'}
    ).execute()
    
    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    logger.info(f"Created pre-doc: {doc_url}")
    return doc_id, doc_url


def create_post_doc(docs_service, drive_service, post_doc_data: dict, topic: str) -> tuple:
    """
    Creates a Google Doc for post-lecture notes.
    Returns (doc_id, doc_url).
    """
    title = post_doc_data.get('title', f'Post-Lecture Notes: {topic}')
    
    doc = docs_service.documents().create(body={'title': title}).execute()
    doc_id = doc['documentId']
    
    content_parts = []
    content_parts.append(f"{title}\n\n")
    
    content_parts.append("📝 Lecture Summary\n")
    content_parts.append(post_doc_data.get('lecture_summary', '') + "\n\n")
    
    content_parts.append("📐 Key Definitions & Formulas\n")
    for item in post_doc_data.get('key_formulas_or_definitions', []):
        content_parts.append(f"• {item}\n")
    content_parts.append("\n")
    
    content_parts.append("💡 Detailed Notes\n")
    for note in post_doc_data.get('detailed_notes', []):
        content_parts.append(f"\n{note.get('heading', '')}\n")
        content_parts.append(note.get('content', '') + "\n")
    content_parts.append("\n")
    
    content_parts.append("⚠️ Common Mistakes to Avoid\n")
    for mistake in post_doc_data.get('common_mistakes', []):
        content_parts.append(f"• {mistake}\n")
    content_parts.append("\n")
    
    content_parts.append("📚 Further Reading\n")
    for ref in post_doc_data.get('further_reading', []):
        content_parts.append(f"• {ref}\n")
    content_parts.append("\n")
    
    content_parts.append("🏋️ Practice Problems\n")
    for i, prob in enumerate(post_doc_data.get('practice_problems', []), 1):
        content_parts.append(f"{i}. {prob}\n")
    
    full_text = "".join(content_parts)
    
    requests = [{'insertText': {'location': {'index': 1}, 'text': full_text}}]
    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
    
    drive_service.permissions().create(
        fileId=doc_id,
        body={'role': 'reader', 'type': 'anyone'}
    ).execute()
    
    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    logger.info(f"Created post-doc: {doc_url}")
    return doc_id, doc_url
