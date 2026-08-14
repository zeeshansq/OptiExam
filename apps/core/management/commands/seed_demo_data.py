from django.core.management.base import BaseCommand
from django.db import transaction
from apps.tenants.models import Tenant, TenantFeatureFlag
from apps.tenants.services.tenant_service import initialize_default_feature_flags
from apps.accounts.models import User, UserRole, UserProfile

class Command(BaseCommand):
    help = 'Seeds initial demo institution and 5 test user accounts for manual testing.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding OptiExam initial demo data...")

        # 1. Create Demo Institution (Tenant)
        tenant, created = Tenant.objects.get_or_create(
            slug='nec',
            defaults={
                'name': 'National Engineering College',
                'tier': Tenant.Tier.PROFESSIONAL,
                'primary_color': '#4F46E5',
                'max_concurrent_candidates': 500,
                'contact_email': 'dean.exams@nec.edu.pk',
                'is_active': True,
            }
        )
        if created:
            initialize_default_feature_flags(tenant)
            self.stdout.write(self.style.SUCCESS(f"Created Tenant: {tenant.name} (slug: {tenant.slug})"))
        else:
            self.stdout.write(f"Tenant '{tenant.name}' already exists.")

        # 2. Create Accounts for All 5 User Roles
        demo_users = [
            {
                'username': 'admin',
                'email': 'admin@optiexam.local',
                'password': 'AdminPass2026!',
                'role': UserRole.SUPER_ADMIN,
                'tenant': None,
                'first_name': 'Global',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
                'reg_no': None,
                'dept': 'SaaS Operations'
            },
            {
                'username': 'designer',
                'email': 'designer@nec.edu',
                'password': 'DesignerPass2026!',
                'role': UserRole.DESIGNER,
                'tenant': tenant,
                'first_name': 'Dr. Sarah',
                'last_name': 'Khan',
                'is_staff': False,
                'is_superuser': False,
                'reg_no': 'FAC-DES-01',
                'dept': 'Academic Examinations'
            },
            {
                'username': 'writer',
                'email': 'writer@nec.edu',
                'password': 'WriterPass2026!',
                'role': UserRole.ITEM_WRITER,
                'tenant': tenant,
                'first_name': 'Prof. Ahmed',
                'last_name': 'Bilal',
                'is_staff': False,
                'is_superuser': False,
                'reg_no': 'FAC-ITW-04',
                'dept': 'Computer Science'
            },
            {
                'username': 'grader',
                'email': 'grader@nec.edu',
                'password': 'GraderPass2026!',
                'role': UserRole.GRADER,
                'tenant': tenant,
                'first_name': 'Ayesha',
                'last_name': 'Malik',
                'is_staff': False,
                'is_superuser': False,
                'reg_no': 'FAC-GRD-09',
                'dept': 'Evaluation Board'
            },
            {
                'username': 'student',
                'email': 'student@nec.edu',
                'password': 'StudentPass2026!',
                'role': UserRole.PARTICIPANT,
                'tenant': tenant,
                'first_name': 'Zaid',
                'last_name': 'Hassan',
                'is_staff': False,
                'is_superuser': False,
                'reg_no': 'STU-2026-0042',
                'dept': 'Software Engineering'
            },
        ]

        for udata in demo_users:
            username = udata['username']
            user, ucreated = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': udata['email'],
                    'role': udata['role'],
                    'tenant': udata['tenant'],
                    'first_name': udata['first_name'],
                    'last_name': udata['last_name'],
                    'is_staff': udata['is_staff'],
                    'is_superuser': udata['is_superuser'],
                    'is_verified': True,
                }
            )
            if ucreated:
                user.set_password(udata['password'])
                user.save()
                UserProfile.objects.create(
                    user=user,
                    registration_number=udata['reg_no'],
                    department=udata['dept'],
                    batch_year='2026'
                )
                self.stdout.write(self.style.SUCCESS(f"Created User: {username} ({udata['role']}) - Pass: {udata['password']}"))
            else:
                self.stdout.write(f"User '{username}' already exists.")

        self.stdout.write(self.style.SUCCESS("\nOptiExam demo data seeding completed successfully!"))
