from django.urls import path
from .views import SampleTemplateDownloadView

app_name = 'core'

urlpatterns = [
    path('templates/<str:template_type>/download/', SampleTemplateDownloadView.as_view(), name='sample_template_download'),
]
