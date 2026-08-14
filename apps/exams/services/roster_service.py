import io
import csv
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from apps.exams.models import Exam, ExamParticipantRoster
from apps.accounts.models import UserRole, UserProfile
from apps.core.models import DataImportJob

User = get_user_model()

def parse_and_validate_roster_rows(file_content: bytes, filename: str) -> Dict[str, Any]:
    """
    Stage 1: Dry-run schema parser and validator for candidate roster uploads.
    Does NOT write to the database.
    """
    rows_data: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    seen_reg_numbers = set()
    seen_emails = set()

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

    required_headers = ['registration_number', 'email']
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
            continue

        row_dict = {}
        for h_idx, header in enumerate(headers):
            if h_idx < len(row_values):
                row_dict[header] = str(row_values[h_idx]).strip() if row_values[h_idx] is not None else ''
            else:
                row_dict[header] = ''

        reg_num = row_dict.get('registration_number', '')
        email = row_dict.get('email', '')
        first_name = row_dict.get('first_name', '')
        last_name = row_dict.get('last_name', '')
        department = row_dict.get('department', '')
        batch_year = row_dict.get('batch_year', '')

        if not reg_num:
            errors.append({'row': row_idx, 'error': "Registration number cannot be blank."})
            continue

        if reg_num in seen_reg_numbers:
            errors.append({'row': row_idx, 'error': f"Duplicate registration number '{reg_num}' found in spreadsheet."})
            continue
        seen_reg_numbers.add(reg_num)

        if not email:
            errors.append({'row': row_idx, 'error': "Email address cannot be blank."})
            continue

        try:
            validate_email(email)
        except ValidationError:
            errors.append({'row': row_idx, 'error': f"Invalid email format: '{email}'."})
            continue

        if email in seen_emails:
            errors.append({'row': row_idx, 'error': f"Duplicate email address '{email}' found in spreadsheet."})
            continue
        seen_emails.add(email)

        rows_data.append({
            'row_number': row_idx,
            'registration_number': reg_num,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'department': department,
            'batch_year': batch_year
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
def commit_roster_import(
    exam: Exam,
    valid_rows: List[Dict[str, Any]],
    user=None,
    source_filename: str = 'roster_upload.csv'
) -> DataImportJob:
    """
    Stage 2: Atomically ingests candidate records, creates accounts if needed,
    and attaches to ExamParticipantRoster with sequential candidate_index.
    """
    job = DataImportJob.objects.create(
        tenant=exam.tenant,
        import_type=DataImportJob.ImportType.PARTICIPANT_ROSTER,
        status=DataImportJob.Status.PROCESSING,
        total_rows=len(valid_rows),
        created_by=user
    )

    current_max_index = (
        ExamParticipantRoster.objects.filter(exam=exam).count()
    )

    created_count = 0
    for item in valid_rows:
        reg_num = item['registration_number']
        email = item['email'].lower()
        first_name = item.get('first_name', '')
        last_name = item.get('last_name', '')
        department = item.get('department', '')
        batch_year = item.get('batch_year', '')

        # Generate username from registration number or email prefix
        clean_username = reg_num.lower().replace(' ', '_').replace('-', '_')

        # Get or create Participant user
        student_user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': clean_username,
                'first_name': first_name,
                'last_name': last_name,
                'tenant': exam.tenant,
                'role': UserRole.PARTICIPANT,
                'is_active': True
            }
        )

        if created:
            student_user.set_unusable_password()
            student_user.save()

        # Update or create user profile
        UserProfile.objects.update_or_create(
            user=student_user,
            defaults={
                'registration_number': reg_num,
                'department': department,
                'batch_year': batch_year
            }
        )

        # Enroll in ExamParticipantRoster if not already enrolled
        if not ExamParticipantRoster.objects.filter(exam=exam, participant=student_user).exists():
            current_max_index += 1
            ExamParticipantRoster.objects.create(
                exam=exam,
                participant=student_user,
                candidate_index=current_max_index,
                registration_number=reg_num,
                status=ExamParticipantRoster.Status.ENROLLED
            )
            created_count += 1

    job.processed_rows = created_count
    job.successful_rows = created_count
    job.status = DataImportJob.Status.COMPLETED
    job.save()
    return job
