from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Built-in Django Admin (Internal Maintenance)
    path('django-admin/', admin.site.urls),

    # Authentication & Profile Hub (/auth/login/, /auth/logout/, etc.)
    path('auth/', include('apps.accounts.urls', namespace='accounts')),

    # Root redirect to login
    path('', RedirectView.as_view(pattern_name='accounts:login', permanent=False), name='index'),

    # Core Global Services & Template Downloads (/core/templates/...)
    path('core/', include('apps.core.urls', namespace='core')),

    # Academic Question Authoring & Repositories (/questions/...)
    path('questions/', include('apps.questions.urls', namespace='questions')),

    # Academic Exam Blueprinting & Rosters (/exams/...)
    path('exams/', include('apps.exams.urls', namespace='exams')),

    # Live Examination Execution & Proctoring (/submissions/...)
    path('submissions/', include('apps.submissions.urls', namespace='submissions')),

    # Distributed Grading & Evaluation Studio (/grading/...)
    path('grading/', include('apps.grading.urls', namespace='grading')),

    # Tenant-Scoped Dashboards & SaaS Workspace
    path('', include('apps.tenants.urls', namespace='tenants')),


]

# Serve media files in local development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
