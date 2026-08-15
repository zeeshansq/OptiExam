from django.urls import path
from .views import SampleTemplateDownloadView, HealthCheckView

app_name = 'core'

urlpatterns = [
    path('healthz/', HealthCheckView.as_view(), name='healthz'),
    path('templates/<str:template_type>/download/', SampleTemplateDownloadView.as_view(), name='sample_template_download'),
]
