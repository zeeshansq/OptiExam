import random
import hashlib
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import PermissionDenied, ValidationError
from apps.exams.models import Exam, ExamSection, ExamQuestionAssignment, ExamParticipantRoster
from apps.submissions.models import ExamAttempt, AttemptAnswer, ProctoringLog
from apps.questions.models import Question, QuestionOption


def generate_candidate_seed(participant_id: int, exam_id: int, is_simulation: bool = False) -> int:
    """
    Computes a deterministic integer seed for reproducible shuffling per candidate.
    If simulation, appends a salt/timestamp to allow re-seeding upon reset.
    """
    if is_simulation:
        raw_seed = f"sim_{participant_id}_{exam_id}_{timezone.now().timestamp()}_{random.randint(1000, 9999)}"
    else:
        raw_seed = f"exam_{participant_id}_{exam_id}"
    digest = hashlib.sha256(raw_seed.encode('utf-8')).hexdigest()
    return int(digest[:12], 16)


@transaction.atomic
def initialize_attempt(
    exam: Exam,
    participant,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    is_simulation: bool = False
) -> ExamAttempt:
    """
    Initializes a new candidate attempt with seeded question/option shuffling,
    or resumes an active attempt if one already exists.
    """
    # For simulations, always purge any old simulation attempt (submitted, expired, in progress) to provide a fresh run
    if is_simulation:
        ExamAttempt.objects.filter(exam=exam, participant=participant, is_simulation=True).delete()
    else:
        # Check for existing IN_PROGRESS attempt
        existing_attempt = ExamAttempt.objects.filter(
            exam=exam,
            participant=participant,
            status=ExamAttempt.Status.IN_PROGRESS,
            is_simulation=False
        ).first()

        if existing_attempt:
            if existing_attempt.is_expired:
                existing_attempt.status = ExamAttempt.Status.AUTO_SUBMITTED
                existing_attempt.submitted_at = timezone.now()
                existing_attempt.save(update_fields=['status', 'submitted_at'])
            else:
                return existing_attempt


    # Enforce Roster verification for non-simulations
    if not is_simulation:
        roster_entry = ExamParticipantRoster.objects.filter(
            exam=exam,
            participant=participant
        ).first()
        if not roster_entry:
            raise PermissionDenied("You are not registered on the official participant roster for this exam.")
        if roster_entry.status != ExamParticipantRoster.Status.ENROLLED:
            raise PermissionDenied(f"Your enrollment status is '{roster_entry.get_status_display()}'. You cannot start this exam.")

    seed = generate_candidate_seed(participant.id, exam.id, is_simulation=is_simulation)
    rng = random.Random(seed)

    attempt = ExamAttempt.objects.create(
        tenant=exam.tenant,
        exam=exam,
        participant=participant,
        candidate_seed=seed,
        started_at=timezone.now(),
        status=ExamAttempt.Status.IN_PROGRESS,
        last_heartbeat=timezone.now(),
        client_ip=client_ip,
        user_agent=user_agent or '',
        is_simulation=is_simulation
    )

    # Collect all assigned questions section-by-section (deduplicated)
    sections = ExamSection.objects.filter(exam=exam).order_by('order')
    ordered_questions: List[Question] = []
    seen_question_ids = set()

    for section in sections:
        assignments = list(ExamQuestionAssignment.objects.filter(section=section).select_related('question').order_by('order'))
        section_questions = []
        for a in assignments:
            if a.question and a.question.id not in seen_question_ids:
                seen_question_ids.add(a.question.id)
                section_questions.append(a.question)

        if exam.shuffle_questions:
            rng.shuffle(section_questions)

        ordered_questions.extend(section_questions)

    # Pre-create blank AttemptAnswer records
    attempt_answers = []
    for order_idx, question in enumerate(ordered_questions, start=1):
        attempt_answers.append(
            AttemptAnswer(
                attempt=attempt,
                question=question,
                order_in_attempt=order_idx
            )
        )
    AttemptAnswer.objects.bulk_create(attempt_answers)

    if ordered_questions:
        attempt.current_question = ordered_questions[0]
        attempt.save(update_fields=['current_question'])

    ProctoringLog.objects.create(
        attempt=attempt,
        event_type=ProctoringLog.EventType.FULLSCREEN_ENTER if exam.enforce_fullscreen else ProctoringLog.EventType.HEARTBEAT_RECONNECTED,
        details={'action': 'attempt_started', 'is_simulation': is_simulation}
    )

    return attempt


@transaction.atomic
def reset_simulation_attempt(exam: Exam, user) -> ExamAttempt:
    """
    Clears any existing simulation attempt for the user and initializes a fresh re-seeded session.
    """
    ExamAttempt.objects.filter(
        exam=exam,
        participant=user,
        is_simulation=True
    ).delete()

    return initialize_attempt(exam=exam, participant=user, is_simulation=True)
