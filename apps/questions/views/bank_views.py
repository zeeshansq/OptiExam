from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from apps.core.mixins import ItemWriterRequiredMixin
from apps.tenants.models import Tenant
from apps.questions.models import QuestionBank
from apps.questions.forms import QuestionBankForm, QuestionBankFilterForm
from apps.questions.selectors.question_selectors import get_tenant_question_banks


class QuestionBankListView(ItemWriterRequiredMixin, ListView):
    model = QuestionBank
    template_name = 'questions/bank_list.html'
    context_object_name = 'banks'
    paginate_by = 10

    def get_paginate_by(self, queryset):
        page_size = self.request.GET.get('page_size', self.paginate_by)
        try:
            val = int(page_size)
            if val in (10, 25, 50, 100):
                return val
        except (ValueError, TypeError):
            pass
        return self.paginate_by

    def get_queryset(self):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant and self.request.user.is_authenticated and self.request.user.is_super_admin():
            tenant = Tenant.objects.filter(is_active=True).first()
        if not tenant:
            return QuestionBank.objects.none()

        q = self.request.GET.get('q', '').strip()
        subject = self.request.GET.get('subject', '').strip()
        return get_tenant_question_banks(tenant=tenant, search_query=q, subject=subject)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = QuestionBankFilterForm(self.request.GET)
        context['active_search_query'] = self.request.GET.get('q', '').strip()
        context['active_subject_filter'] = self.request.GET.get('subject', '').strip()
        return context


class QuestionBankCreateView(ItemWriterRequiredMixin, CreateView):
    model = QuestionBank
    form_class = QuestionBankForm
    template_name = 'questions/bank_form.html'

    def form_valid(self, form):
        tenant = getattr(self.request, 'tenant', None)
        if not tenant and self.request.user.is_super_admin():
            tenant = Tenant.objects.filter(is_active=True).first()
        form.instance.tenant = tenant
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Question Bank '{form.instance.name}' created successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('questions:bank_detail', kwargs={'bank_id': self.object.pk})


class QuestionBankUpdateView(ItemWriterRequiredMixin, UpdateView):
    model = QuestionBank
    form_class = QuestionBankForm
    template_name = 'questions/bank_form.html'
    pk_url_kwarg = 'bank_id'

    def get_queryset(self):
        return QuestionBank.objects.for_tenant(self.request.tenant)

    def form_valid(self, form):
        messages.success(self.request, f"Question Bank '{form.instance.name}' updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('questions:bank_detail', kwargs={'bank_id': self.object.pk})


class QuestionBankDeleteView(ItemWriterRequiredMixin, DeleteView):
    model = QuestionBank
    template_name = 'questions/bank_confirm_delete.html'
    pk_url_kwarg = 'bank_id'
    success_url = reverse_lazy('questions:bank_list')

    def get_queryset(self):
        return QuestionBank.objects.for_tenant(self.request.tenant)

    def form_valid(self, form):
        bank_name = self.get_object().name
        messages.warning(self.request, f"Question Bank '{bank_name}' and all its questions have been removed.")
        return super().form_valid(form)
