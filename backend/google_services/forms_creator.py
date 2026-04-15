"""
Creates Google Forms quiz from AI-generated quiz data.
"""
import logging
import random

logger = logging.getLogger(__name__)


def create_quiz_form(forms_service, drive_service, quiz_data: dict) -> tuple:
    """
    Creates a Google Form quiz with all questions.
    Returns (form_id, form_url).
    """
    title = quiz_data.get('title', 'Quiz')
    
    # Step 1: Create the form
    form_body = {
        'info': {
            'title': title,
            'documentTitle': title,
        }
    }
    form = forms_service.forms().create(body=form_body).execute()
    form_id = form['formId']
    
    # Step 2: Enable quiz mode + add questions in one batchUpdate
    requests = [
        {
            'updateSettings': {
                'settings': {'quizSettings': {'isQuiz': True}},
                'updateMask': 'quizSettings.isQuiz'
            }
        }
    ]
    
    questions = quiz_data.get('questions', [])
    
    for i, q in enumerate(questions):
        q_type = q.get('type', 'MCQ').upper()
        marks = int(q.get('marks', 1))
        options = q.get('options', [])
        correct = q.get('correct_answer', '')
        explanation = q.get('explanation', '')
        
        # Shuffle options in the backend to ensure randomized positions
        if options:
            random.shuffle(options)
        
        if q_type in ('MCQ', 'MIXED') and options:
            # Multiple choice question
            choice_options = [{'value': opt} for opt in options]
            
            # Find correct answer option
            correct_options = []
            for opt in options:
                if opt.startswith(correct + ')') or opt == correct:
                    correct_options.append({'value': opt})
                    break
            if not correct_options and options:
                correct_options = [{'value': options[0]}]
            
            item = {
                'createItem': {
                    'item': {
                        'title': q.get('question_text', f'Question {i+1}'),
                        'questionItem': {
                            'question': {
                                'required': True,
                                'grading': {
                                    'pointValue': marks,
                                    'correctAnswers': {'answers': correct_options},
                                    'whenRight': {'text': explanation or 'Correct!'},
                                    'whenWrong': {'text': f"Correct answer: {correct}. {explanation}"},
                                },
                                'choiceQuestion': {
                                    'type': 'RADIO',
                                    'options': choice_options,
                                    'shuffle': True,
                                }
                            }
                        }
                    },
                    'location': {'index': i}
                }
            }
        else:
            # Short answer question
            item = {
                'createItem': {
                    'item': {
                        'title': q.get('question_text', f'Question {i+1}'),
                        'questionItem': {
                            'question': {
                                'required': True,
                                'grading': {'pointValue': marks},
                                'textQuestion': {'paragraph': False}
                            }
                        }
                    },
                    'location': {'index': i}
                }
            }
        
        requests.append(item)
    
    # Execute batchUpdate
    forms_service.forms().batchUpdate(
        formId=form_id,
        body={'requests': requests}
    ).execute()
    
    # Set sharing (allow anyone with link to view/respond)
    drive_service.permissions().create(
        fileId=form_id,
        body={'role': 'writer', 'type': 'anyone'}
    ).execute()
    
    # Get edit URL for teacher (they can get response URL from there)
    form_url = f"https://docs.google.com/forms/d/{form_id}/edit"
    logger.info(f"Created quiz form: {form_url}")
    return form_id, form_url
