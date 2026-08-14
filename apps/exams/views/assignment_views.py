from django.views.generic import View
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from apps.core.mixins import DesignerRequiredMixin
from apps.exams.models import Exam, ExamSection, ExamQuestionAssignment
from apps.questions.models import Question, QuestionBank
from apps.exams.services.exam_lifecycle_service import assign_question_to_section, remove_question_from_section
from apps.questions.selectors.question_selectors import get_tenant_question_banks

class QuestionPickerPaletteView(DesignerRequiredMixin, View):
    """
    Full-width interactive Question Picker palette allowing the Designer
    to assign items from any tenant Question Bank into a specific ExamSection.
    """
    template_name = 'exams/question_picker.html'

    def get_section(self, section_id):
        return get_object_or_404(
            ExamSection.objects.filter(exam__tenant=self.request.tenant),
            pk=section_id
        )

    def get(self, request, section_id, *args, **kwargs):
        section = self.get_section(section_id)
        tenant = request.tenant
        banks = get_tenant_question_banks(tenant=tenant)
        
        selected_bank_id = request.GET.get('bank')
        questions = Question.objects.for_tenant(tenant)
        if selected_bank_id:
            questions = questions.filter(bank_id=selected_bank_id)
        
        assigned_question_ids = section.assignments.values_list('question_id', flat=True)

        return render(request, self.template_name, {
            'section': section,
            'exam': section.exam,
            'banks': banks,
            'selected_bank_id': selected_bank_id,
            'questions': questions.prefetch_related('options'),
            'assigned_question_ids': set(assigned_question_ids)
        })

    def post(self, request, section_id, *args, **kwargs):
        section = self.get_section(section_id)
        question_id = request.POST.get('question_id')
        custom_marks = request.POST.get('custom_marks')

        question = get_object_or_404(Question.objects.for_tenant(request.tenant), pk=question_id)
        custom_pts = None
        if custom_marks:
            from decimal import Decimal
            try:
                custom_pts = Decimal(custom_marks)
            except Exception:
                pass

        assign_question_to_section(section, question, custom_marks=custom_pts)
        messages.success(request, f"Question Q#{question.pk} assigned to {section.title}.")
        return redirect('exams:question_picker', section_id=section.pk)


class QuestionRemoveAssignmentView(DesignerRequiredMixin, View):
    def post(self, request, assignment_id, *args, **kwargs):
        assignment = get_object_or_404(
            ExamQuestionAssignment.objects.filter(section__exam__tenant=request.tenant),
            pk=assignment_id
        )
        section = assignment.section
        assignment.delete()
        messages.warning(request, "Question removed from section.")
        return redirect('exams:exam_detail', exam_id=section.exam.pk)
