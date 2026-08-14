import json
from django.views import View
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from apps.core.mixins import ItemWriterRequiredMixin
from apps.questions.models import QuestionBank
from apps.questions.forms import QuestionImportForm
from apps.questions.services.question_import_service import (
    parse_and_validate_question_rows,
    commit_question_import
)

class QuestionBankImportView(ItemWriterRequiredMixin, View):
    """
    Two-Stage Question Bank Import Hub:
    Stage 1: Dry-run schema validation (0 DB writes) -> 10-row preview & error table.
    Stage 2: Atomic commit to active QuestionBank.
    """
    template_name = 'questions/question_import.html'

    def get_bank(self, bank_id):
        return get_object_or_404(
            QuestionBank.objects.for_tenant(self.request.tenant),
            pk=bank_id
        )

    def get(self, request, bank_id, *args, **kwargs):
        bank = self.get_bank(bank_id)
        form = QuestionImportForm()
        return render(request, self.template_name, {
            'bank': bank,
            'form': form,
            'stage': 'upload'
        })

    def post(self, request, bank_id, *args, **kwargs):
        bank = self.get_bank(bank_id)
        action = request.POST.get('action', 'validate')

        if action == 'validate':
            form = QuestionImportForm(request.POST, request.FILES)
            if form.is_valid():
                uploaded_file = request.FILES['file']
                file_bytes = uploaded_file.read()
                filename = uploaded_file.name

                validation_result = parse_and_validate_question_rows(file_bytes, filename)
                
                # Store valid rows temporarily in session for Stage 2 commit
                if validation_result['valid_rows']:
                    # Convert Decimal to str for JSON serialization in session
                    serialized_rows = []
                    for r in validation_result['valid_rows']:
                        row_copy = dict(r)
                        row_copy['points'] = str(r['points'])
                        row_copy['negative_points'] = str(r['negative_points'])
                        if 'rubrics' in row_copy:
                            for rub in row_copy['rubrics']:
                                rub['max_points'] = str(rub['max_points'])
                        serialized_rows.append(row_copy)
                    request.session['staged_question_rows'] = serialized_rows
                    request.session['staged_filename'] = filename
                else:
                    request.session.pop('staged_question_rows', None)

                return render(request, self.template_name, {
                    'bank': bank,
                    'form': form,
                    'stage': 'preview',
                    'result': validation_result,
                    'filename': filename
                })

        elif action == 'commit':
            staged_rows = request.session.get('staged_question_rows', [])
            filename = request.session.get('staged_filename', 'questions.csv')
            if not staged_rows:
                messages.error(request, "No staged question data found to commit. Please re-upload.")
                return redirect('questions:bank_import', bank_id=bank.pk)

            # Re-convert Decimal values
            from decimal import Decimal
            clean_rows = []
            for r in staged_rows:
                row_copy = dict(r)
                row_copy['points'] = Decimal(r['points'])
                row_copy['negative_points'] = Decimal(r['negative_points'])
                if 'rubrics' in row_copy:
                    for rub in row_copy['rubrics']:
                        rub['max_points'] = Decimal(rub['max_points'])
                clean_rows.append(row_copy)

            job = commit_question_import(
                bank=bank,
                valid_rows=clean_rows,
                user=request.user,
                source_filename=filename
            )

            # Clear session
            request.session.pop('staged_question_rows', None)
            request.session.pop('staged_filename', None)

            messages.success(request, f"Successfully imported {job.successful_rows} questions into '{bank.name}'.")
            return redirect('questions:bank_detail', bank_id=bank.pk)

        return redirect('questions:bank_import', bank_id=bank.pk)
