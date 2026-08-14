import io
import csv
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List, Optional
from django.db import transaction
from apps.questions.models import QuestionBank, Question, QuestionOption, QuestionRubric
from apps.core.models import DataImportJob

def parse_and_validate_question_rows(file_content: bytes, filename: str) -> Dict[str, Any]:
    """
    Stage 1: Dry-run schema parser and validator for question bank uploads.
    Does NOT write to the database.
    """
    rows_data: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    try:
        if filename.endswith('.xlsx'):
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)
            ws = wb.active
            rows_iter = ws.iter_rows(values_only=True)
            headers = [str(h).strip().lower() if h else '' for h in next(rows_iter, [])]
            raw_rows = list(rows_iter)
        else:
            decoded = file_content.decode('utf-8-sig', errors='replace')
            reader = csv.reader(io.StringIO(decoded))
            headers = [h.strip().lower() for h in next(reader, [])]
            raw_rows = list(reader)
    except Exception as e:
        return {
            'valid': False,
            'total_rows': 0,
            'valid_count': 0,
            'errors': [{'row': 0, 'error': f"Failed to parse file: {str(e)}"}],
            'preview_rows': [],
            'valid_rows': []
        }

    required_headers = ['question_type', 'prompt', 'points']
    for req in required_headers:
        if req not in headers:
            errors.append({'row': 1, 'error': f"Missing mandatory column header: '{req}'"})

    if errors:
        return {
            'valid': False,
            'total_rows': 0,
            'valid_count': 0,
            'errors': errors,
            'preview_rows': [],
            'valid_rows': []
        }

    for row_idx, row_values in enumerate(raw_rows, start=2):
        if not any(row_values):
            continue  # Skip empty rows

        row_dict = {}
        for h_idx, header in enumerate(headers):
            if h_idx < len(row_values):
                row_dict[header] = str(row_values[h_idx]).strip() if row_values[h_idx] is not None else ''
            else:
                row_dict[header] = ''

        q_type = row_dict.get('question_type', '').upper()
        if q_type not in Question.QuestionType.values:
            errors.append({
                'row': row_idx,
                'error': f"Invalid question_type '{q_type}'. Must be one of: {', '.join(Question.QuestionType.values)}"
            })
            continue

        prompt = row_dict.get('prompt', '')
        if not prompt:
            errors.append({'row': row_idx, 'error': "Question prompt cannot be blank."})
            continue

        try:
            points = Decimal(row_dict.get('points', '1.0'))
        except (InvalidOperation, ValueError):
            errors.append({'row': row_idx, 'error': f"Invalid points value '{row_dict.get('points')}'."})
            continue

        try:
            neg_points = Decimal(row_dict.get('negative_points', '0.0') or '0.0')
        except (InvalidOperation, ValueError):
            neg_points = Decimal('0.0')

        diff = row_dict.get('difficulty', 'MEDIUM').upper()
        if diff not in Question.Difficulty.values:
            diff = Question.Difficulty.MEDIUM

        blooms = row_dict.get('blooms_level', 'REMEMBER').upper()
        if blooms not in Question.BloomsLevel.values:
            blooms = Question.BloomsLevel.REMEMBER

        # Parse options for MCQ formats
        parsed_options = []
        options_raw = row_dict.get('options', '')
        correct_raw = [c.strip().upper() for c in row_dict.get('correct_options', '').split(',') if c.strip()]

        if q_type in (Question.QuestionType.MCQ_SINGLE, Question.QuestionType.MCQ_MULTIPLE, Question.QuestionType.IMAGE_MCQ):
            if options_raw:
                raw_opts_list = [o.strip() for o in options_raw.split('|') if o.strip()]
                for opt_idx, opt_text in enumerate(raw_opts_list):
                    # Option text might look like "A) Option 1"
                    letter = chr(65 + opt_idx)  # A, B, C, D...
                    is_corr = (letter in correct_raw) or (str(opt_idx + 1) in correct_raw)
                    # Clean out prefix if present
                    clean_text = opt_text
                    if len(opt_text) > 3 and opt_text[1:3] in (') ', '. '):
                        clean_text = opt_text[3:].strip()

                    parsed_options.append({
                        'option_text': clean_text,
                        'is_correct': is_corr,
                        'order': opt_idx
                    })

            if len(parsed_options) < 2:
                errors.append({'row': row_idx, 'error': "MCQ questions must include at least 2 choice options separated by '|'."})
                continue

            correct_count = sum(1 for o in parsed_options if o['is_correct'])
            if q_type == Question.QuestionType.MCQ_SINGLE and correct_count != 1:
                errors.append({
                    'row': row_idx,
                    'error': f"Single Choice MCQ must specify exactly 1 correct option (found {correct_count})."
                })
                continue
            elif q_type == Question.QuestionType.MCQ_MULTIPLE and correct_count < 1:
                errors.append({
                    'row': row_idx,
                    'error': "Multiple Choice MCQ must specify at least 1 correct option."
                })
                continue

        # Parse rubric criteria for essay questions
        parsed_rubrics = []
        rubrics_raw = row_dict.get('rubric_criteria', '')
        if rubrics_raw and q_type == Question.QuestionType.LONG_ESSAY:
            for r_idx, r_item in enumerate(rubrics_raw.split('|')):
                if ':' in r_item:
                    title, r_pts = r_item.rsplit(':', 1)
                    try:
                        pts_val = Decimal(r_pts.strip())
                    except Exception:
                        pts_val = Decimal('1.0')
                    parsed_rubrics.append({
                        'criteria_title': title.strip(),
                        'description': '',
                        'max_points': pts_val,
                        'order': r_idx
                    })

        rows_data.append({
            'row_number': row_idx,
            'question_type': q_type,
            'prompt': prompt,
            'points': points,
            'negative_points': neg_points,
            'difficulty': diff,
            'blooms_level': blooms,
            'topic_tags': row_dict.get('topic_tags', ''),
            'model_answer': row_dict.get('model_answer', ''),
            'hint_text': row_dict.get('hint_text', ''),
            'options': parsed_options,
            'rubrics': parsed_rubrics
        })

    is_valid = len(errors) == 0 and len(rows_data) > 0
    return {
        'valid': is_valid,
        'total_rows': len(rows_data) + len(errors),
        'valid_count': len(rows_data),
        'errors': errors,
        'preview_rows': rows_data[:10],
        'valid_rows': rows_data
    }


@transaction.atomic
def commit_question_import(
    bank: QuestionBank,
    valid_rows: List[Dict[str, Any]],
    user=None,
    source_filename: str = 'questions_upload.csv'
) -> DataImportJob:
    """
    Stage 2: Commits validated question rows into the database atomically.
    """
    job = DataImportJob.objects.create(
        tenant=bank.tenant,
        import_type=DataImportJob.ImportType.QUESTION_BANK,
        status=DataImportJob.Status.PROCESSING,
        total_rows=len(valid_rows),
        created_by=user
    )

    created_count = 0
    for item in valid_rows:
        q = Question.objects.create(
            tenant=bank.tenant,
            bank=bank,
            question_type=item['question_type'],
            prompt=item['prompt'],
            points=item['points'],
            negative_points=item['negative_points'],
            difficulty=item['difficulty'],
            blooms_level=item['blooms_level'],
            topic_tags=item['topic_tags'],
            model_answer=item['model_answer'],
            hint_text=item['hint_text'],
            created_by=user
        )

        for opt in item.get('options', []):
            QuestionOption.objects.create(
                question=q,
                option_text=opt['option_text'],
                is_correct=opt['is_correct'],
                order=opt['order']
            )

        for rub in item.get('rubrics', []):
            QuestionRubric.objects.create(
                question=q,
                criteria_title=rub['criteria_title'],
                description=rub.get('description', ''),
                max_points=rub['max_points'],
                order=rub['order']
            )

        created_count += 1

    job.processed_rows = created_count
    job.successful_rows = created_count
    job.status = DataImportJob.Status.COMPLETED
    job.save()
    return job
