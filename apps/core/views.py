from django.http import HttpResponse, Http404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from apps.core.services.template_service import (
    generate_sample_roster_template,
    generate_sample_question_bank_template
)

class SampleTemplateDownloadView(LoginRequiredMixin, View):
    """
    Delivers dynamic, validated sample CSV/XLSX template files for bulk imports.
    """
    def get(self, request, template_type, *args, **kwargs):
        format_type = request.GET.get('format', 'csv').lower()
        if format_type not in ('csv', 'xlsx'):
            format_type = 'csv'

        if template_type == 'roster':
            content, content_type, filename = generate_sample_roster_template(format_type)
        elif template_type == 'questions':
            content, content_type, filename = generate_sample_question_bank_template(format_type)
        else:
            raise Http404("Sample template type not recognized.")

        response = HttpResponse(content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
