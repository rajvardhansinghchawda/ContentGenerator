"""
Creates and formats Google Docs for pre-doc and post-doc content.
"""
import logging

logger = logging.getLogger(__name__)

def _get_image_uri(file_id):
    # This thumbnail URI format is the most reliable for embedding Drive images into Docs
    return f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"

def _apply_professional_template(docs_service, doc_id, job, pre_doc_data=None, post_doc_data=None):
    """
    Applies the professional branded template:
    1. Branded Header (Logo)
    2. Metadata Table (structured, navy blue labels, bold header row)
    3. Branded Footer (Contact Info)
    """
    teacher = job.teacher

    # Professional Color (Navy Blue)
    BLUE_COLOR = {'color': {'rgbColor': {'red': 0.12, 'green': 0.23, 'blue': 0.54}}}

    # ── Step 1: Create Header/Footer zones ──────────────────────────────────
    header_id = ""
    footer_id = ""
    setup_reqs = []
    if teacher.header_image_id:
        setup_reqs.append({'createHeader': {'type': 'DEFAULT'}})
    if teacher.footer_image_id:
        setup_reqs.append({'createFooter': {'type': 'DEFAULT'}})

    if setup_reqs:
        try:
            res = docs_service.documents().batchUpdate(
                documentId=doc_id, body={'requests': setup_reqs}
            ).execute()
            for reply in res.get('replies', []):
                if 'createHeader' in reply:
                    header_id = reply['createHeader']['headerId']
                if 'createFooter' in reply:
                    footer_id = reply['createFooter']['footerId']
            logger.info(f"Header ID: {header_id}, Footer ID: {footer_id}")
        except Exception as e:
            logger.error(f"Header/footer creation failed: {e}")
            try:
                doc = docs_service.documents().get(documentId=doc_id).execute()
                header_id = list(doc.get('headers', {}).keys())[0] if doc.get('headers') else ""
                footer_id = list(doc.get('footers', {}).keys())[0] if doc.get('footers') else ""
            except Exception as e2:
                logger.error(f"Fallback header/footer fetch failed: {e2}")

    # ── Step 2: Insert Metadata Table ────────────────────────────────────────
    try:
        docs_service.documents().batchUpdate(documentId=doc_id, body={
            'requests': [{'insertTable': {'rows': 9, 'columns': 4, 'location': {'index': 1}}}]
        }).execute()
    except Exception as e:
        logger.error(f"Table creation failed: {e}")
        return

    # ── Step 3: Fetch table structure & fill data ────────────────────────────
    updated_doc = docs_service.documents().get(documentId=doc_id).execute()
    table_element = next(el for el in updated_doc['body']['content'] if 'table' in el)
    table = table_element['table']
    table_start_index = table_element['startIndex']

    def cell_text_index(r, c):
        return table['tableRows'][r]['tableCells'][c]['content'][0]['startIndex']

    template_data = [
        (8, 1, ", ".join(pre_doc_data.get('expected_outcomes', [])) if pre_doc_data else "N/A"),
        (8, 0, "Learning Outcomes:"),
        (7, 1, ", ".join(pre_doc_data.get('learning_objectives', [])) if pre_doc_data else "N/A"),
        (7, 0, "Learning Objectives:"),
        (6, 1, job.topic), (6, 0, "Title of the Lecture:"),
        (4, 0, f"Lecture No: {job.lecture_no}"),
        (3, 3, job.subject_code or "N/A"), (3, 2, "Subject Code:"),
        (3, 1, job.subject_name or "Generic"), (3, 0, "Subject:"),
        (2, 3, job.semester), (2, 2, "Semester:"),
        (2, 1, teacher.full_name), (2, 0, "Name of Faculty:"),
        (1, 3, job.session), (1, 2, "Session:"),
        (1, 1, teacher.department), (1, 0, "Department:"),
        (0, 0, f"{teacher.institution} - Academic Resources")
    ]

    fill_requests = []
    # Merge institution header row
    fill_requests.append({'mergeTableCells': {'tableRange': {'tableCellLocation': {
        'tableStartLocation': {'index': table_start_index}, 'rowIndex': 0, 'columnIndex': 0},
        'rowSpan': 1, 'columnSpan': 4}}})
    # Merge Lecture No row
    fill_requests.append({'mergeTableCells': {'tableRange': {'tableCellLocation': {
        'tableStartLocation': {'index': table_start_index}, 'rowIndex': 4, 'columnIndex': 0},
        'rowSpan': 1, 'columnSpan': 4}}})
    # Merge value columns for content rows
    for row in [5, 6, 7, 8]:
        fill_requests.append({'mergeTableCells': {'tableRange': {'tableCellLocation': {
            'tableStartLocation': {'index': table_start_index}, 'rowIndex': row, 'columnIndex': 1},
            'rowSpan': 1, 'columnSpan': 3}}})

    for r, c, txt in template_data:
        fill_requests.append({'insertText': {'location': {'index': cell_text_index(r, c)}, 'text': txt}})

    try:
        docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': fill_requests}).execute()
    except Exception as e:
        logger.warning(f"Merging/Filling failed: {e}")

    # ── Step 4: Apply Styles (Colors + Bold) ─────────────────────────────────
    final_doc = docs_service.documents().get(documentId=doc_id).execute()
    final_table = next(el['table'] for el in final_doc['body']['content'] if 'table' in el)

    def get_text_range(r, c):
        """Returns the range of the actual text paragraph inside a cell."""
        cell = final_table['tableRows'][r]['tableCells'][c]
        para = cell['content'][0]
        return {
            'startIndex': para['startIndex'],
            'endIndex': para.get('endIndex', para['startIndex'] + 1)
        }

    style_requests = []

    # Row 0: Institution header — centered, bold, navy blue, large
    r0_range = get_text_range(0, 0)
    style_requests.append({'updateParagraphStyle': {
        'range': r0_range,
        'paragraphStyle': {'alignment': 'CENTER'},
        'fields': 'alignment'
    }})
    style_requests.append({'updateTextStyle': {
        'range': r0_range,
        'textStyle': {**BLUE_COLOR, 'bold': True, 'fontSize': {'magnitude': 14, 'unit': 'PT'}},
        'fields': 'foregroundColor,bold,fontSize'
    }})

    # Row 4: Lecture No — centered, bold, navy blue
    r4_range = get_text_range(4, 0)
    style_requests.append({'updateParagraphStyle': {
        'range': r4_range,
        'paragraphStyle': {'alignment': 'CENTER'},
        'fields': 'alignment'
    }})
    style_requests.append({'updateTextStyle': {
        'range': r4_range,
        'textStyle': {**BLUE_COLOR, 'bold': True},
        'fields': 'foregroundColor,bold'
    }})

    # All label cells — bold + navy blue
    label_cells = [
        (1, 0), (1, 2),   # Department:, Session:
        (2, 0), (2, 2),   # Name of Faculty:, Semester:
        (3, 0), (3, 2),   # Subject:, Subject Code:
        (5, 0), (6, 0), (7, 0), (8, 0)  # content labels
    ]
    for r, c in label_cells:
        try:
            rng = get_text_range(r, c)
            style_requests.append({'updateTextStyle': {
                'range': rng,
                'textStyle': {**BLUE_COLOR, 'bold': True},
                'fields': 'foregroundColor,bold'
            }})
        except Exception:
            pass

    try:
        docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': style_requests}).execute()
        logger.info("Styling applied successfully.")
    except Exception as e:
        logger.warning(f"Styling failed: {e}")

    # ── Step 5: Insert Branding Images (isolated call) ───────────────────────
    branding_requests = []
    if header_id and teacher.header_image_id:
        logger.info(f"Inserting header image: {teacher.header_image_id}")
        branding_requests.append({
            'insertInlineImage': {
                'uri': _get_image_uri(teacher.header_image_id),
                'location': {'segmentId': header_id, 'index': 0},
                'objectSize': {'width': {'magnitude': 468, 'unit': 'PT'}}
            }
        })
    if footer_id and teacher.footer_image_id:
        logger.info(f"Inserting footer image: {teacher.footer_image_id}")
        branding_requests.append({
            'insertInlineImage': {
                'uri': _get_image_uri(teacher.footer_image_id),
                'location': {'segmentId': footer_id, 'index': 0},
                'objectSize': {'width': {'magnitude': 468, 'unit': 'PT'}}
            }
        })
    if branding_requests:
        try:
            docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': branding_requests}).execute()
            logger.info("Branding images inserted successfully.")
        except Exception as e:
            logger.error(f"Branding image insertion failed: {e}")


def create_pre_doc(docs_service, drive_service, pre_doc_data: dict, job) -> tuple:
    title = pre_doc_data.get('title', f'Pre-Lecture Notes: {job.topic}')
    doc = docs_service.documents().create(body={'title': title}).execute()
    doc_id = doc['documentId']

    # Apply Branded Template
    _apply_professional_template(docs_service, doc_id, job, pre_doc_data=pre_doc_data)

    # Build rest of content (starts after the table, roughly index 300+ after filling)
    # To be safe, we'll append to the end
    content_parts = []
    content_parts.append(f"\n\n{title.upper()}\n")
    content_parts.append("\n📚 Prerequisite Knowledge\n")
    for prereq in pre_doc_data.get('prerequisite_topics', []):
        content_parts.append(f"• {prereq}\n")
    
    content_parts.append("\n📖 Introduction\n")
    content_parts.append(pre_doc_data.get('introduction', '') + "\n\n")
    
    content_parts.append("🔑 Key Concepts\n")
    for kc in pre_doc_data.get('key_concepts', []):
        content_parts.append(f"• {kc.get('concept', '')}: {kc.get('brief_explanation', '')}\n")
    
    content_parts.append("\n📋 Pre-Reading Material\n")
    content_parts.append(pre_doc_data.get('pre_reading_material', '') + "\n")
    
    full_text = "".join(content_parts)
    
    # Get current length to append at the end
    doc_curr = docs_service.documents().get(documentId=doc_id).execute()
    last_index = doc_curr['body']['content'][-1]['endIndex'] - 1
    
    requests = [{'insertText': {'location': {'index': last_index}, 'text': full_text}}]
    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
    
    drive_service.permissions().create(fileId=doc_id, body={'role': 'reader', 'type': 'anyone'}).execute()
    return doc_id, f"https://docs.google.com/document/d/{doc_id}/edit"

def create_post_doc(docs_service, drive_service, post_doc_data: dict, job) -> tuple:
    title = post_doc_data.get('title', f'Post-Lecture Notes: {job.topic}')
    doc = docs_service.documents().create(body={'title': title}).execute()
    doc_id = doc['documentId']

    # Apply Branded Template
    _apply_professional_template(docs_service, doc_id, job, post_doc_data=post_doc_data)

    content_parts = []
    content_parts.append(f"\n\n{title.upper()}\n")
    content_parts.append("\n📝 Lecture Summary\n")
    content_parts.append(post_doc_data.get('lecture_summary', '') + "\n")
    
    content_parts.append("\n📐 Key Definitions & Formulas\n")
    for item in post_doc_data.get('key_formulas_or_definitions', []):
        content_parts.append(f"• {item}\n")
    
    content_parts.append("\n💡 Detailed Notes\n")
    for note in post_doc_data.get('detailed_notes', []):
        content_parts.append(f"\n{note.get('heading', '')}\n")
        content_parts.append(note.get('content', '') + "\n")
    
    content_parts.append("\n⚠️ Common Mistakes to Avoid\n")
    for mistake in post_doc_data.get('common_mistakes', []):
        content_parts.append(f"• {mistake}\n")
    
    content_parts.append("\n📚 Further Reading\n")
    for ref in post_doc_data.get('further_reading', []):
        content_parts.append(f"• {ref}\n")
    
    content_parts.append("\n🏋️ Practice Problems\n")
    for i, prob in enumerate(post_doc_data.get('practice_problems', []), 1):
        content_parts.append(f"{i}. {prob}\n")

    full_text = "".join(content_parts)
    
    doc_curr = docs_service.documents().get(documentId=doc_id).execute()
    last_index = doc_curr['body']['content'][-1]['endIndex'] - 1
    
    requests = [{'insertText': {'location': {'index': last_index}, 'text': full_text}}]
    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
    
    drive_service.permissions().create(fileId=doc_id, body={'role': 'reader', 'type': 'anyone'}).execute()
    return doc_id, f"https://docs.google.com/document/d/{doc_id}/edit"
