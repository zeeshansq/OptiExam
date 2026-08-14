from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from apps.tenants.models import Tenant
from apps.tenants.services.tenant_service import initialize_default_feature_flags
from apps.accounts.models import User, UserRole, UserProfile
from apps.questions.models import QuestionBank, Question, QuestionOption, QuestionRubric
from apps.exams.models import Exam, ExamSection, ExamQuestionAssignment, ExamLifelineConfig, ExamParticipantRoster
from apps.questions.services.question_service import create_question

class Command(BaseCommand):
    help = 'Seeds initial demo institution, 5 test user accounts, question banks, and exam blueprints.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding OptiExam Phase 1 & Phase 2 demo data...")

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

        user_instances = {}
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
                )
                self.stdout.write(self.style.SUCCESS(f"Created User: {user.username} ({user.role})"))
            else:
                self.stdout.write(f"User '{user.username}' already exists.")
            user_instances[username] = user

        # 3. Create Demo Question Banks
        bank_cs, _ = QuestionBank.objects.get_or_create(
            tenant=tenant,
            name="Computer Science Fundamentals",
            defaults={
                'code': 'CS101-BANK',
                'subject': 'Computer Science',
                'description': 'Curated items covering complexity analysis, linear & tree structures, and OOP principles.',
                'created_by': user_instances['writer']
            }
        )

        bank_dsa, _ = QuestionBank.objects.get_or_create(
            tenant=tenant,
            name="Data Structures & Algorithms",
            defaults={
                'code': 'DSA-BANK',
                'subject': 'Algorithms',
                'description': 'Advanced algorithmic design, graph theory, and dynamic programming items.',
                'created_by': user_instances['writer']
            }
        )

        # 4. Seed Questions into Bank CS
        if bank_cs.questions.count() == 0:
            # Q1: Single Choice MCQ
            q1 = create_question(
                bank=bank_cs,
                prompt="What is the worst-case asymptotic time complexity of Merge Sort on an array of size n?",
                question_type=Question.QuestionType.MCQ_SINGLE,
                points=Decimal('2.0'),
                negative_points=Decimal('0.5'),
                difficulty=Question.Difficulty.MEDIUM,
                blooms_level=Question.BloomsLevel.UNDERSTAND,
                topic_tags='sorting, algorithms, complexity',
                model_answer='Merge Sort divides the array into halves log(n) times and takes O(n) work per level.',
                hint_text='Think of recursion tree depth and linear work per level.',
                created_by=user_instances['writer'],
                options_data=[
                    {'option_text': 'O(n)', 'is_correct': False},
                    {'option_text': 'O(n log n)', 'is_correct': True, 'explanation': 'T(n) = 2T(n/2) + O(n) solves to O(n log n).'},
                    {'option_text': 'O(n^2)', 'is_correct': False},
                    {'option_text': 'O(log n)', 'is_correct': False},
                ]
            )

            # Q2: Multiple Choice MCQ
            q2 = create_question(
                bank=bank_cs,
                prompt="Which of the following data structures inherently maintain linear sequential storage? (Select all that apply)",
                question_type=Question.QuestionType.MCQ_MULTIPLE,
                points=Decimal('3.0'),
                negative_points=Decimal('1.0'),
                difficulty=Question.Difficulty.EASY,
                blooms_level=Question.BloomsLevel.REMEMBER,
                topic_tags='data-structures, linear',
                model_answer='Arrays, Stacks, and Queues are linear. Trees and Graphs are non-linear hierarchical/mesh structures.',
                created_by=user_instances['writer'],
                options_data=[
                    {'option_text': 'Array', 'is_correct': True},
                    {'option_text': 'Binary Search Tree', 'is_correct': False},
                    {'option_text': 'Queue', 'is_correct': True},
                    {'option_text': 'Directed Graph', 'is_correct': False},
                    {'option_text': 'Stack', 'is_correct': True},
                ]
            )

            # Q3: Short Answer
            q3 = create_question(
                bank=bank_cs,
                prompt="Define the term 'virtual memory' and explain its primary benefit to multitasking operating systems.",
                question_type=Question.QuestionType.SHORT_ANSWER,
                points=Decimal('5.0'),
                difficulty=Question.Difficulty.MEDIUM,
                blooms_level=Question.BloomsLevel.UNDERSTAND,
                topic_tags='os, virtual-memory, paging',
                model_answer='Virtual memory maps process logical addresses to physical RAM using page tables, providing isolation and memory expansion via swap space.',
                hint_text='Focus on address translation and process isolation.',
                created_by=user_instances['writer']
            )

            # Q4: Long Essay with Rubric
            q4 = create_question(
                bank=bank_cs,
                prompt="Explain Dijkstra's Single-Source Shortest Path algorithm. Include priority queue usage, edge relaxation mechanics, and time complexity derivation.",
                question_type=Question.QuestionType.LONG_ESSAY,
                points=Decimal('10.0'),
                difficulty=Question.Difficulty.HARD,
                blooms_level=Question.BloomsLevel.CREATE,
                topic_tags='graphs, dijkstra, algorithms',
                model_answer='Initialization: dist[s]=0, all others inf. Extract-min using min-heap. Relax edges (u,v): if dist[v] > dist[u] + w(u,v) then dist[v] = dist[u] + w(u,v). Overall complexity O((V+E) log V).',
                created_by=user_instances['writer'],
                rubrics_data=[
                    {'criteria_title': 'Algorithm Principles & State Setup', 'description': 'Initial distances and priority queue setup', 'max_points': Decimal('3.0')},
                    {'criteria_title': 'Edge Relaxation Step & Proof', 'description': 'Greedy relaxation formula correctness', 'max_points': Decimal('4.0')},
                    {'criteria_title': 'Asymptotic Time Complexity Derivation', 'description': 'Accurate derivation of binary heap vs Fibonacci heap bound', 'max_points': Decimal('3.0')},
                ]
            )
            self.stdout.write(self.style.SUCCESS("Seeded 4 questions with options and rubrics into CS101-BANK."))

        # 5. Create Demo Exam Blueprint
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=4)

        exam, ecreated = Exam.objects.get_or_create(
            tenant=tenant,
            code='CS101-MID-2026',
            defaults={
                'title': 'Midterm Assessment: Data Structures & Algorithms',
                'subject': 'Computer Science',
                'description': 'Official Spring 2026 Midterm Examination.',
                'instructions': 'Full-screen mode is strictly enforced. Closing window or switching tabs will log an anti-cheating violation.',
                'start_time': start_time,
                'end_time': end_time,
                'duration_minutes': 90,
                'total_marks': Decimal('100.0'),
                'passing_percentage': Decimal('40.0'),
                'enforce_fullscreen': True,
                'lock_copy_paste': True,
                'shuffle_questions': True,
                'shuffle_options': True,
                'allow_back_navigation': True,
                'max_tab_switch_limit': 3,
                'created_by': user_instances['designer']
            }
        )

        if ecreated:
            # Create default sections
            sec_a = ExamSection.objects.create(
                exam=exam,
                title="Section A — Objective MCQs",
                description="Answer all multiple choice questions.",
                order=1,
                weightage=Decimal('40.0')
            )
            sec_b = ExamSection.objects.create(
                exam=exam,
                title="Section B — Structured Essay Problems",
                description="Detailed derivations and explanations.",
                order=2,
                weightage=Decimal('60.0')
            )

            # Assign questions to sections
            for q in bank_cs.questions.filter(question_type__in=[Question.QuestionType.MCQ_SINGLE, Question.QuestionType.MCQ_MULTIPLE]):
                ExamQuestionAssignment.objects.create(section=sec_a, question=q, order=1)

            for q in bank_cs.questions.filter(question_type__in=[Question.QuestionType.SHORT_ANSWER, Question.QuestionType.LONG_ESSAY]):
                ExamQuestionAssignment.objects.create(section=sec_b, question=q, order=1)

            # Initialize lifelines
            for lt in ExamLifelineConfig.LifelineType.values:
                ExamLifelineConfig.objects.create(
                    exam=exam,
                    lifeline_type=lt,
                    is_enabled=True,
                    max_allowed=1
                )

            # Enroll demo student into candidate roster with candidate_index = 1
            ExamParticipantRoster.objects.create(
                exam=exam,
                participant=user_instances['student'],
                candidate_index=1,
                registration_number='STU-2026-0042',
                status=ExamParticipantRoster.Status.ENROLLED
            )
            self.stdout.write(self.style.SUCCESS(f"Created Exam Blueprint: {exam.title} ({exam.code}) with sections, questions & student roster."))

        self.stdout.write(self.style.SUCCESS("\n[OK] Phase 1 & Phase 2 Demo Seeding Completed Successfully!"))
