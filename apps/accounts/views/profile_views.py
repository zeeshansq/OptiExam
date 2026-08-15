from django.views.generic import UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib import messages
from apps.accounts.models import User, UserProfile
from apps.accounts.forms import UserProfileForm

class UserProfileView(LoginRequiredMixin, UpdateView):
    """
    Profile management view for updating contact info and bio.
    """
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_initial(self):
        initial = super().get_initial()
        initial['first_name'] = self.request.user.first_name
        initial['last_name'] = self.request.user.last_name
        initial['email'] = self.request.user.email
        return initial

    def form_valid(self, form):
        user = self.request.user
        user.first_name = form.cleaned_data.get('first_name', '')
        user.last_name = form.cleaned_data.get('last_name', '')
        user.email = form.cleaned_data.get('email', '')
        user.save()
        messages.success(self.request, "Profile details updated successfully.")
        return super().form_valid(form)

class ThemeToggleView(LoginRequiredMixin, View):
    """
    Toggles the dark/light UI theme stored in the user's session.
    """
    def post(self, request, *args, **kwargs):
        current_theme = request.session.get('ui_theme', 'dark')
        new_theme = 'light' if current_theme == 'dark' else 'dark'
        request.session['ui_theme'] = new_theme
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({'status': 'success', 'theme': new_theme})
        return redirect(request.META.get('HTTP_REFERER', '/'))


class MarkNotificationsReadView(LoginRequiredMixin, View):
    """
    AJAX endpoint to mark in-app notifications as read.
    POST: marks all unread notifications for current user as read.
    POST with `notification_id` in body: marks a specific one.
    """
    def post(self, request, *args, **kwargs):
        from apps.accounts.models import Notification
        import json
        try:
            body = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            body = {}

        notification_id = body.get('notification_id')
        if notification_id:
            updated = Notification.objects.filter(
                user=request.user, id=notification_id
            ).update(is_read=True)
        else:
            # Mark all as read
            updated = Notification.objects.filter(
                user=request.user, is_read=False
            ).update(is_read=True)

        return JsonResponse({'status': 'success', 'marked_read': updated})

