from django.urls import path
from apps.accounts.views import auth_views, profile_views

app_name = 'accounts'

urlpatterns = [
    # Authentication routes
    path('login/', auth_views.OptiExamLoginView.as_view(), name='login'),
    path('logout/', auth_views.OptiExamLogoutView.as_view(), name='logout'),
    path('role-redirect/', auth_views.RoleRedirectView.as_view(), name='role_redirect'),

    # Profile & Preferences
    path('profile/', profile_views.UserProfileView.as_view(), name='profile'),
    path('theme-toggle/', profile_views.ThemeToggleView.as_view(), name='theme_toggle'),
]
