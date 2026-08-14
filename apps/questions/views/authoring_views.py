from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.contrib import messages
from apps.core.mixins import ItemWriterRequiredMixin
from apps.questions.models import QuestionBank, Question, QuestionOption, QuestionRubric
from apps.questions.forms import (
    QuestionBaseForm,
    QuestionOptionFormSet,
    QuestionRubricFormSet,
    QuestionFilterForm
)
from apps.questions.selectors.question_selectors import get_bank_questions
from apps.questions.services.question_service import duplicate_question

class QuestionListView(ItemWriterRequiredMixin, ListView):
    model = Question
    template_name = 'questions/question_list.html'
    context_object_name = 'questions'
    paginate_by = 15

    def get_bank(self):
        return get_object_or_404(
            QuestionBank.objects.for_tenant(self.request.tenant),
            pk=self.kwargs['bank_id']
        )

    def get_paginate_by(self, queryset):
        page_size = self.request.GET.get('page_size', self.paginate_by)
        try:
            val = int(page_size)
            if val in (10, 15, 25, 50, 100):
                return val
        except (ValueError, TypeError):
            pass
        return self.paginate_by

    def get_queryset(self):
        bank = self.get_bank()
        q = self.request.GET.get('q', '').strip()
        q_type = self.request.GET.get('question_type', '').strip()
        diff = self.request.GET.get('difficulty', '').strip()
        blooms = self.request.GET.get('blooms_level', '').strip()
        sort_by = self.request.GET.get('sort', '-created_at')
        if self.request.GET.get('order') == 'asc' and not sort_by.startswith('-'):
            pass
        elif self.request.GET.get('order') == 'desc' and not sort_by.startswith('-'):
            sort_by = f"-{sort_by}"

        return get_bank_questions(
            bank=bank,
            search_query=q,
            question_type=q_type,
            difficulty=diff,
            blooms_level=blooms,
            sort_by=sort_by
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bank'] = self.get_bank()
        context['filter_form'] = QuestionFilterForm(self.request.GET)
        context['active_search_query'] = self.request.GET.get('q', '').strip()
        context['active_type_filter'] = self.request.GET.get('question_type', '').strip()
        context['active_difficulty_filter'] = self.request.GET.get('difficulty', '').strip()
        context['active_blooms_filter'] = self.request.GET.get('blooms_level', '').strip()
        return context


class QuestionCreateMCQView(ItemWriterRequiredMixin, View):
    """
    Balanced 2-Column Authoring Studio for MCQ questions with dynamic Option Formset.
    """
    template_name = 'questions/question_form_mcq.html'

    def get_bank(self):
        return get_object_or_404(
            QuestionBank.objects.for_tenant(self.request.tenant),
            pk=self.kwargs['bank_id']
        )

    def get(self, request, bank_id, *args, **kwargs):
        bank = self.get_bank()
        q_type = request.GET.get('type', Question.QuestionType.MCQ_SINGLE)
        initial = {'bank': bank, 'question_type': q_type, 'points': 1.0, 'difficulty': Question.Difficulty.MEDIUM}
        form = QuestionBaseForm(initial=initial, tenant=request.tenant)
        formset = QuestionOptionFormSet(instance=Question(bank=bank, question_type=q_type))
        return render(request, self.template_name, {'bank': bank, 'form': form, 'formset': formset, 'is_create': True})

    def post(self, request, bank_id, *args, **kwargs):
        bank = self.get_bank()
        form = QuestionBaseForm(request.POST, request.FILES, tenant=request.tenant)
        if form.is_valid():
            question = form.save(commit=False)
            question.tenant = request.tenant
            question.bank = bank
            question.created_by = request.user
            formset = QuestionOptionFormSet(request.POST, request.FILES, instance=question)
            if formset.is_valid():
                question.save()
                formset.save()
                messages.success(request, "Multiple-choice question created successfully.")
                return redirect('questions:bank_detail', bank_id=bank.pk)
        else:
            formset = QuestionOptionFormSet(request.POST, request.FILES)

        return render(request, self.template_name, {'bank': bank, 'form': form, 'formset': formset, 'is_create': True})


class QuestionUpdateMCQView(ItemWriterRequiredMixin, View):
    template_name = 'questions/question_form_mcq.html'

    def get_object(self):
        return get_object_or_404(
            Question.objects.for_tenant(self.request.tenant),
            pk=self.kwargs['question_id']
        )

    def get(self, request, question_id, *args, **kwargs):
        question = self.get_object()
        form = QuestionBaseForm(instance=question, tenant=request.tenant)
        formset = QuestionOptionFormSet(instance=question)
        return render(request, self.template_name, {'bank': question.bank, 'question': question, 'form': form, 'formset': formset, 'is_create': False})

    def post(self, request, question_id, *args, **kwargs):
        question = self.get_object()
        form = QuestionBaseForm(request.POST, request.FILES, instance=question, tenant=request.tenant)
        formset = QuestionOptionFormSet(request.POST, request.FILES, instance=question)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Question updated successfully.")
            return redirect('questions:bank_detail', bank_id=question.bank.pk)

        return render(request, self.template_name, {'bank': question.bank, 'question': question, 'form': form, 'formset': formset, 'is_create': False})


class QuestionCreateSubjectiveView(ItemWriterRequiredMixin, View):
    """
    Balanced 2-Column Authoring Studio for Short Answer and Long Essay questions with Rubric Formset.
    """
    template_name = 'questions/question_form_subjective.html'

    def get_bank(self):
        return get_object_or_404(
            QuestionBank.objects.for_tenant(self.request.tenant),
            pk=self.kwargs['bank_id']
        )

    def get(self, request, bank_id, *args, **kwargs):
        bank = self.get_bank()
        q_type = request.GET.get('type', Question.QuestionType.LONG_ESSAY)
        initial = {'bank': bank, 'question_type': q_type, 'points': 5.0, 'difficulty': Question.Difficulty.MEDIUM}
        form = QuestionBaseForm(initial=initial, tenant=request.tenant)
        formset = QuestionRubricFormSet(instance=Question(bank=bank, question_type=q_type, points=5.0))
        return render(request, self.template_name, {'bank': bank, 'form': form, 'formset': formset, 'is_create': True})

    def post(self, request, bank_id, *args, **kwargs):
        bank = self.get_bank()
        form = QuestionBaseForm(request.POST, request.FILES, tenant=request.tenant)
        if form.is_valid():
            question = form.save(commit=False)
            question.tenant = request.tenant
            question.bank = bank
            question.created_by = request.user
            formset = QuestionRubricFormSet(request.POST, instance=question)
            if formset.is_valid():
                question.save()
                formset.save()
                messages.success(request, "Subjective question authored successfully.")
                return redirect('questions:bank_detail', bank_id=bank.pk)
        else:
            formset = QuestionRubricFormSet(request.POST)

        return render(request, self.template_name, {'bank': bank, 'form': form, 'formset': formset, 'is_create': True})


class QuestionUpdateSubjectiveView(ItemWriterRequiredMixin, View):
    template_name = 'questions/question_form_subjective.html'

    def get_object(self):
        return get_object_or_404(
            Question.objects.for_tenant(self.request.tenant),
            pk=self.kwargs['question_id']
        )

    def get(self, request, question_id, *args, **kwargs):
        question = self.get_object()
        form = QuestionBaseForm(instance=question, tenant=request.tenant)
        formset = QuestionRubricFormSet(instance=question)
        return render(request, self.template_name, {'bank': question.bank, 'question': question, 'form': form, 'formset': formset, 'is_create': False})

    def post(self, request, question_id, *args, **kwargs):
        question = self.get_object()
        form = QuestionBaseForm(request.POST, request.FILES, instance=question, tenant=request.tenant)
        formset = QuestionRubricFormSet(request.POST, instance=question)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Subjective question updated successfully.")
            return redirect('questions:bank_detail', bank_id=question.bank.pk)

        return render(request, self.template_name, {'bank': question.bank, 'question': question, 'form': form, 'formset': formset, 'is_create': False})


class QuestionDetailView(ItemWriterRequiredMixin, DetailView):
    model = Question
    template_name = 'questions/question_detail.html'
    pk_url_kwarg = 'question_id'
    context_object_name = 'question'

    def get_queryset(self):
        return Question.objects.for_tenant(self.request.tenant).prefetch_related('options', 'rubrics')


class QuestionDuplicateView(ItemWriterRequiredMixin, View):
    def post(self, request, question_id, *args, **kwargs):
        question = get_object_or_404(
            Question.objects.for_tenant(request.tenant),
            pk=question_id
        )
        cloned = duplicate_question(question)
        messages.success(request, f"Question duplicated as Q#{cloned.id}.")
        return redirect('questions:bank_detail', bank_id=question.bank.pk)


class QuestionDeleteView(ItemWriterRequiredMixin, DeleteView):
    model = Question
    template_name = 'questions/question_confirm_delete.html'
    pk_url_kwarg = 'question_id'

    def get_queryset(self):
        return Question.objects.for_tenant(self.request.tenant)

    def get_success_url(self):
        return reverse('questions:bank_detail', kwargs={'bank_id': self.object.bank.pk})

    def form_valid(self, form):
        messages.warning(self.request, "Question deleted from bank.")
        return super().form_valid(form)
