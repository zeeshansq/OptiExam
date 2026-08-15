from django.core.management.base import BaseCommand
from apps.submissions.services.submission_service import auto_submit_expired_attempts


class Command(BaseCommand):
    help = "Scans and automatically submits all expired in-progress exam attempts."

    def handle(self, *args, **options):
        self.stdout.write("Running auto-submit sweep for expired exam attempts...")
        submitted_count = auto_submit_expired_attempts()
        self.stdout.write(self.style.SUCCESS(f"Successfully processed and auto-submitted {submitted_count} expired attempt(s)."))
