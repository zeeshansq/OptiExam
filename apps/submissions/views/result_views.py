from decimal import Decimal
import hashlib
from django.views.generic import View
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Count, Q
from apps.exams.models import Exam
from apps.submissions.models import ExamAttempt, AttemptAnswer
from apps.grading.models import QuestionScore, GradeModeration


class ExamResultView(LoginRequiredMixin, View):
    """
    Participant Official Scorecard, Academic Analytics & Certificate View with print support.
    """
    template_name = 'submissions/exam_result.html'

    def get(self, request, exam_id, *args, **kwargs):
        exam = get_object_or_404(
            Exam.objects.for_tenant(request.tenant),
            pk=exam_id
        )

        # Access Guard: results must be published
        if not exam.results_published and not (request.user.is_designer() or request.user.is_super_admin()):
            return render(request, 'submissions/result_pending.html', {'exam': exam})

        attempt = ExamAttempt.objects.filter(
            exam=exam,
            participant=request.user,
            is_simulation=False
        ).select_related('grade_moderation').first()

        if not attempt:
            raise PermissionDenied("No examination attempt found for your account.")

        answers = list(
            AttemptAnswer.objects.filter(attempt=attempt)
            .select_related('question')
            .prefetch_related('selected_options', 'question__options')
            .order_by('order_in_attempt')
        )

        moderation = getattr(attempt, 'grade_moderation', None)
        final_score = moderation.total_final_score if moderation and moderation.total_final_score is not None else Decimal('0.00')
        percentage = ((final_score / exam.total_marks) * Decimal('100.00')).quantize(Decimal('0.01')) if exam.total_marks > 0 else Decimal('0.00')
        is_passed = moderation.is_passed if moderation else (percentage >= exam.passing_percentage)

        # Determine Academic Letter Grade & Honors
        if percentage >= Decimal('90.00'):
            letter_grade = 'A+'
            grade_remark = 'Outstanding Academic Distinction'
            honor_badge = 'Gold Tier Distinction'
        elif percentage >= Decimal('85.00'):
            letter_grade = 'A'
            grade_remark = 'Excellent Mastery'
            honor_badge = 'High Honors'
        elif percentage >= Decimal('80.00'):
            letter_grade = 'A-'
            grade_remark = 'Very Good'
            honor_badge = 'Honors'
        elif percentage >= Decimal('75.00'):
            letter_grade = 'B+'
            grade_remark = 'Good Performance'
            honor_badge = 'Merit'
        elif percentage >= Decimal('70.00'):
            letter_grade = 'B'
            grade_remark = 'Above Average'
            honor_badge = 'Merit'
        elif percentage >= Decimal('60.00'):
            letter_grade = 'C'
            grade_remark = 'Satisfactory'
            honor_badge = 'Standard Pass'
        elif percentage >= Decimal('50.00'):
            letter_grade = 'D'
            grade_remark = 'Marginal Pass'
            honor_badge = 'Pass'
        else:
            letter_grade = 'F'
            grade_remark = 'Did Not Meet Minimum Benchmark'
            honor_badge = 'Unsatisfactory'

        # Collect question-level score breakdown & stats
        total_questions = len(answers)
        correct_count = 0
        partial_count = 0
        incorrect_count = 0
        unattempted_count = 0
        mcq_points_earned = Decimal('0.00')
        subjective_points_earned = Decimal('0.00')
        blooms_breakdown = {}

        question_breakdown = []
        for ans in answers:
            q = ans.question
            score_record = QuestionScore.objects.filter(answer=ans).first()
            awarded = ans.marks_awarded if ans.marks_awarded is not None else (score_record.awarded_marks if score_record else Decimal('0.00'))
            has_responded = bool(ans.text_response or ans.selected_options.exists())

            if not has_responded:
                unattempted_count += 1
                status = 'UNATTEMPTED'
            elif awarded >= q.points:
                correct_count += 1
                status = 'FULL'
            elif awarded > 0:
                partial_count += 1
                status = 'PARTIAL'
            else:
                incorrect_count += 1
                status = 'INCORRECT'

            if q.is_mcq:
                mcq_points_earned += max(Decimal('0.00'), awarded)
            else:
                subjective_points_earned += max(Decimal('0.00'), awarded)

            # Cognitive taxonomy distribution
            b_level = q.get_blooms_level_display()
            if b_level not in blooms_breakdown:
                blooms_breakdown[b_level] = {'total_pts': Decimal('0.00'), 'earned_pts': Decimal('0.00'), 'count': 0}
            blooms_breakdown[b_level]['total_pts'] += q.points
            blooms_breakdown[b_level]['earned_pts'] += max(Decimal('0.00'), awarded)
            blooms_breakdown[b_level]['count'] += 1

            question_breakdown.append({
                'answer': ans,
                'question': q,
                'score_record': score_record,
                'awarded': awarded,
                'status': status,
                'correct_options': q.options.filter(is_correct=True) if q.is_mcq else None
            })

        # Section-wise Analytics
        section_analytics = []
        for sec in exam.sections.all():
            sec_answers = [item for item in question_breakdown if item['question'].exam_assignments.filter(section=sec).exists()]
            sec_max = sum((item['question'].points for item in sec_answers), Decimal('0.00'))
            sec_earned = sum((item['awarded'] for item in sec_answers), Decimal('0.00'))
            sec_pct = ((sec_earned / sec_max) * Decimal('100.00')).quantize(Decimal('0.1')) if sec_max > 0 else Decimal('0.00')
            section_analytics.append({
                'section': sec,
                'total_questions': len(sec_answers),
                'max_points': sec_max,
                'earned_points': sec_earned,
                'percentage': sec_pct
            })

        # Cohort Rank & Percentile
        all_attempts = list(
            ExamAttempt.objects.filter(exam=exam, is_simulation=False)
            .select_related('grade_moderation')
        )
        scores_list = []
        for a in all_attempts:
            m = getattr(a, 'grade_moderation', None)
            s = m.total_final_score if m and m.total_final_score is not None else Decimal('0.00')
            scores_list.append(s)
        scores_list.sort(reverse=True)

        rank = scores_list.index(final_score) + 1 if final_score in scores_list else 1
        total_candidates = max(1, len(scores_list))

        # Standard Psychometric Percentile Rank Formula:
        # Percentile = ((Candidates Scored Below + 0.5 * Candidates Tied) / Total Candidates) * 100
        # If tied for 1st place in top tier, this correctly reflects top ~90-100th percentile standing.
        below_count = sum(1 for s in scores_list if s < final_score)
        tied_count = sum(1 for s in scores_list if s == final_score)
        percentile = (((Decimal(below_count) + (Decimal('0.5') * Decimal(tied_count))) / Decimal(total_candidates)) * Decimal('100.00')).quantize(Decimal('0.1'))



        # Certificate Verification Hash
        raw_token = f"OPTIEXAM-CERT-{request.tenant.slug}-{exam.code}-{attempt.participant.username}-{attempt.pk}-{final_score}"
        certificate_id = f"CERT-{exam.code[:4]}-{attempt.pk:05d}-{hashlib.sha256(raw_token.encode()).hexdigest()[:8].upper()}"

        # Exam Time Duration Elapsed
        time_spent_mins = 0
        if attempt.started_at and attempt.submitted_at:
            time_spent_mins = max(1, int((attempt.submitted_at - attempt.started_at).total_seconds() / 60))

        context = {
            'exam': exam,
            'attempt': attempt,
            'moderation': moderation,
            'question_breakdown': question_breakdown,
            'show_feedback': exam.show_grader_feedback,
            'final_score': final_score,
            'percentage': percentage,
            'letter_grade': letter_grade,
            'grade_remark': grade_remark,
            'honor_badge': honor_badge,
            'is_passed': is_passed,
            'total_questions': total_questions,
            'correct_count': correct_count,
            'partial_count': partial_count,
            'incorrect_count': incorrect_count,
            'unattempted_count': unattempted_count,
            'mcq_points_earned': mcq_points_earned,
            'subjective_points_earned': subjective_points_earned,
            'section_analytics': section_analytics,
            'blooms_breakdown': blooms_breakdown,
            'rank': rank,
            'total_candidates': total_candidates,
            'percentile': percentile,
            'certificate_id': certificate_id,
            'time_spent_mins': time_spent_mins
        }
        return render(request, self.template_name, context)

