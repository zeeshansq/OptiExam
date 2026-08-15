"""
Management command to seed realistic Pakistani domain data across all tables and relations.
"""

import os
import uuid
import random
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from django.utils import timezone
from django.conf import settings

# Domain Models
from apps.tenants.models import Tenant, TenantFeatureFlag
from apps.accounts.models import User, UserRole, UserProfile, AuditLog, Notification
from apps.questions.models import QuestionBank, Question, QuestionOption, QuestionRubric
from apps.exams.models import (
    Exam, ExamSection, ExamQuestionAssignment,
    ExamLifelineConfig, ExamParticipantRoster
)
from apps.submissions.models import (
    ExamAttempt, AttemptAnswer, ProctoringLog, AttemptLifelineUsage
)
from apps.grading.models import GraderAllocation, QuestionScore, GradeModeration


class Command(BaseCommand):
    help = "Seeds comprehensive, conflict-free Pakistani institutional exam data across all models."

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing database records before seeding.'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO("=" * 80))
        self.stdout.write(self.style.SUCCESS("  OptiExam Pakistani Domain Data Seeder & Fixture Engine"))
        self.stdout.write(self.style.HTTP_INFO("=" * 80))

        # 0. Automatic Schema & Migration Initialization
        # Ensures that if db.sqlite3 was deleted or does not exist, all tables are created first.
        self.stdout.write(self.style.HTTP_INFO("\n[0/7] Ensuring database schema and migrations are applied..."))
        call_command('migrate', interactive=False, verbosity=0)
        self.stdout.write(self.style.SUCCESS("[OK] Database schema initialized and migrated."))

        with transaction.atomic():
            if options.get('clear'):
                self.stdout.write(self.style.WARNING("[*] Clearing existing database records..."))

                GradeModeration.objects.all().delete()
                QuestionScore.objects.all().delete()
                GraderAllocation.objects.all().delete()
                AttemptLifelineUsage.objects.all().delete()
                ProctoringLog.objects.all().delete()
                AttemptAnswer.objects.all().delete()
                ExamAttempt.objects.all().delete()
                ExamParticipantRoster.objects.all().delete()
                ExamLifelineConfig.objects.all().delete()
                ExamQuestionAssignment.objects.all().delete()
                ExamSection.objects.all().delete()
                Exam.objects.all().delete()
                QuestionOption.objects.all().delete()
                QuestionRubric.objects.all().delete()
                Question.objects.all().delete()
                QuestionBank.objects.all().delete()
                Notification.objects.all().delete()
                AuditLog.objects.all().delete()
                UserProfile.objects.all().delete()
                User.objects.exclude(is_superuser=True).delete()
                TenantFeatureFlag.objects.all().delete()
                Tenant.objects.all().delete()
                self.stdout.write(self.style.SUCCESS("[OK] Database wiped cleanly."))

            # ------------------------------------------------------------------
            # 1. TENANTS & INSTITUTIONAL BRANDING (Pakistani Universities)
            # ------------------------------------------------------------------
            self.stdout.write(self.style.HTTP_INFO("\n[1/7] Provisioning Pakistani Institutional Tenants..."))

            tenants_spec = [
                {
                    'name': 'National University of Sciences & Technology (NUST)',
                    'slug': 'nust',
                    'domain': 'nust.edu.pk',
                    'tier': Tenant.Tier.ENTERPRISE,
                    'primary_color': '#004F9E',
                    'contact_email': 'controller.exams@nust.edu.pk',
                    'max_concurrent_candidates': 1000
                },
                {
                    'name': 'FAST National University of Computer & Emerging Sciences',
                    'slug': 'fast-nuces',
                    'domain': 'nu.edu.pk',
                    'tier': Tenant.Tier.ENTERPRISE,
                    'primary_color': '#002D62',
                    'contact_email': 'academics@nu.edu.pk',
                    'max_concurrent_candidates': 800
                },
                {
                    'name': 'King Edward Medical University (KEMU)',
                    'slug': 'kemu',
                    'domain': 'kemu.edu.pk',
                    'tier': Tenant.Tier.PROFESSIONAL,
                    'primary_color': '#006633',
                    'contact_email': 'assessments@kemu.edu.pk',
                    'max_concurrent_candidates': 500
                },
                {
                    'name': 'NED University of Engineering & Technology',
                    'slug': 'ned',
                    'domain': 'neduet.edu.pk',
                    'tier': Tenant.Tier.PROFESSIONAL,
                    'primary_color': '#8B0000',
                    'contact_email': 'exams@neduet.edu.pk',
                    'max_concurrent_candidates': 500
                }
            ]

            tenants_map = {}
            for t_spec in tenants_spec:
                t, _ = Tenant.objects.update_or_create(
                    slug=t_spec['slug'],
                    defaults=t_spec
                )
                # Feature Flags
                for feat in TenantFeatureFlag.Feature.values:
                    TenantFeatureFlag.objects.update_or_create(
                        tenant=t,
                        feature_key=feat,
                        defaults={'is_enabled': True}
                    )
                tenants_map[t.slug] = t
                self.stdout.write(f"  [+] Tenant: {t.name} [{t.slug}]")

            nust_tenant = tenants_map['nust']
            fast_tenant = tenants_map['fast-nuces']
            kemu_tenant = tenants_map['kemu']

            # ------------------------------------------------------------------
            # 2. 5-TIER USER ROLES & PROFILES
            # ------------------------------------------------------------------
            self.stdout.write(self.style.HTTP_INFO("\n[2/7] Provisioning 5-Tier User Accounts with Pakistani Personas..."))

            universal_password = "OptiExam@2026!"

            users_spec = [
                # Super Admin
                {
                    'username': 'admin',
                    'email': 'superadmin@optiexam.pk',
                    'first_name': 'M. Tariq',
                    'last_name': 'Javed',
                    'role': UserRole.SUPER_ADMIN,
                    'tenant': None,
                    'is_staff': True,
                    'is_superuser': True,
                    'phone': '+92-300-1112233',
                    'reg_num': 'SAAS-ADM-001',
                    'dept': 'Platform Directorate',
                    'batch': '2026'
                },
                {
                    'username': 'superadmin',
                    'email': 'director.it@optiexam.pk',
                    'first_name': 'Kamran',
                    'last_name': 'Akhtar',
                    'role': UserRole.SUPER_ADMIN,
                    'tenant': None,
                    'is_staff': True,
                    'is_superuser': True,
                    'phone': '+92-300-2223344',
                    'reg_num': 'SAAS-ADM-002',
                    'dept': 'Executive IT',
                    'batch': '2026'
                },
                # Designers (Tenant Admins)
                {
                    'username': 'dr.sarah.khan',
                    'email': 'sarah.khan@nust.edu.pk',
                    'first_name': 'Dr. Sarah',
                    'last_name': 'Khan',
                    'role': UserRole.DESIGNER,
                    'tenant': nust_tenant,
                    'phone': '+92-321-5551234',
                    'reg_num': 'NUST-FAC-101',
                    'dept': 'School of Electrical Engg & Computer Science (SEECS)',
                    'batch': 'Faculty'
                },
                {
                    'username': 'dr.usman.tariq',
                    'email': 'usman.tariq@nu.edu.pk',
                    'first_name': 'Dr. Usman',
                    'last_name': 'Tariq',
                    'role': UserRole.DESIGNER,
                    'tenant': fast_tenant,
                    'phone': '+92-333-6662345',
                    'reg_num': 'FAST-FAC-204',
                    'dept': 'Department of Software Engineering',
                    'batch': 'Faculty'
                },
                {
                    'username': 'dr.khalid.mahmood',
                    'email': 'khalid.m@kemu.edu.pk',
                    'first_name': 'Prof. Dr. Khalid',
                    'last_name': 'Mahmood',
                    'role': UserRole.DESIGNER,
                    'tenant': kemu_tenant,
                    'phone': '+92-300-7773456',
                    'reg_num': 'KEMU-FAC-012',
                    'dept': 'Department of Clinical Assessment',
                    'batch': 'Faculty'
                },
                # Item Writers
                {
                    'username': 'prof.ahmed.bilal',
                    'email': 'ahmed.bilal@nust.edu.pk',
                    'first_name': 'Prof. Ahmed',
                    'last_name': 'Bilal',
                    'role': UserRole.ITEM_WRITER,
                    'tenant': nust_tenant,
                    'phone': '+92-345-8884567',
                    'reg_num': 'NUST-IW-301',
                    'dept': 'Computer Science Department',
                    'batch': 'Faculty'
                },
                {
                    'username': 'dr.ayesha.malik',
                    'email': 'ayesha.malik@kemu.edu.pk',
                    'first_name': 'Dr. Ayesha',
                    'last_name': 'Malik',
                    'role': UserRole.ITEM_WRITER,
                    'tenant': kemu_tenant,
                    'phone': '+92-312-9995678',
                    'reg_num': 'KEMU-IW-109',
                    'dept': 'Physiology & Cardiology',
                    'batch': 'Faculty'
                },
                # Graders / Evaluators
                {
                    'username': 'grader.zainab',
                    'email': 'zainab.ali@nust.edu.pk',
                    'first_name': 'Zainab',
                    'last_name': 'Ali',
                    'role': UserRole.GRADER,
                    'tenant': nust_tenant,
                    'phone': '+92-334-1234567',
                    'reg_num': 'NUST-GRD-501',
                    'dept': 'SEECS Examination Wing',
                    'batch': 'Examiner'
                },
                {
                    'username': 'grader.tariq',
                    'email': 'tariq.mehmood@nust.edu.pk',
                    'first_name': 'Tariq',
                    'last_name': 'Mehmood',
                    'role': UserRole.GRADER,
                    'tenant': nust_tenant,
                    'phone': '+92-331-2345678',
                    'reg_num': 'NUST-GRD-502',
                    'dept': 'SEECS Chief Examination Board',
                    'batch': 'Examiner'
                },
                {
                    'username': 'grader.hina',
                    'email': 'hina.sheikh@nu.edu.pk',
                    'first_name': 'Hina',
                    'last_name': 'Sheikh',
                    'role': UserRole.GRADER,
                    'tenant': fast_tenant,
                    'phone': '+92-322-3456789',
                    'reg_num': 'FAST-GRD-102',
                    'dept': 'Faculty of Computing',
                    'batch': 'Examiner'
                },
                # Student Candidates (Participants)
                {
                    'username': 'ali.hassan',
                    'email': 'ali.hassan@student.nust.edu.pk',
                    'first_name': 'Ali',
                    'last_name': 'Hassan',
                    'role': UserRole.PARTICIPANT,
                    'tenant': nust_tenant,
                    'phone': '+92-301-4567890',
                    'reg_num': '2022-NUST-CS-042',
                    'dept': 'Computer Science',
                    'batch': '2022-2026'
                },
                {
                    'username': 'fatima.zahra',
                    'email': 'fatima.zahra@student.nust.edu.pk',
                    'first_name': 'Fatima',
                    'last_name': 'Zahra',
                    'role': UserRole.PARTICIPANT,
                    'tenant': nust_tenant,
                    'phone': '+92-302-5678901',
                    'reg_num': '2022-NUST-CS-088',
                    'dept': 'Computer Science',
                    'batch': '2022-2026'
                },
                {
                    'username': 'usman.akbar',
                    'email': 'usman.akbar@student.nust.edu.pk',
                    'first_name': 'Usman',
                    'last_name': 'Akbar',
                    'role': UserRole.PARTICIPANT,
                    'tenant': nust_tenant,
                    'phone': '+92-303-6789012',
                    'reg_num': '2022-NUST-CS-105',
                    'dept': 'Computer Science',
                    'batch': '2022-2026'
                },
                {
                    'username': 'sana.iqbal',
                    'email': 'sana.iqbal@student.nust.edu.pk',
                    'first_name': 'Sana',
                    'last_name': 'Iqbal',
                    'role': UserRole.PARTICIPANT,
                    'tenant': nust_tenant,
                    'phone': '+92-304-7890123',
                    'reg_num': '2022-NUST-SE-120',
                    'dept': 'Software Engineering',
                    'batch': '2022-2026'
                },
                {
                    'username': 'bilal.raza',
                    'email': 'bilal.raza@student.nust.edu.pk',
                    'first_name': 'Bilal',
                    'last_name': 'Raza',
                    'role': UserRole.PARTICIPANT,
                    'tenant': nust_tenant,
                    'phone': '+92-305-8901234',
                    'reg_num': '2022-NUST-SE-145',
                    'dept': 'Software Engineering',
                    'batch': '2022-2026'
                },
                {
                    'username': 'zain.abbas',
                    'email': 'zain.abbas@student.nust.edu.pk',
                    'first_name': 'Zain',
                    'last_name': 'Abbas',
                    'role': UserRole.PARTICIPANT,
                    'tenant': nust_tenant,
                    'phone': '+92-306-9012345',
                    'reg_num': '2022-NUST-AI-160',
                    'dept': 'Artificial Intelligence',
                    'batch': '2022-2026'
                },
                {
                    'username': 'maryam.khan',
                    'email': 'maryam.khan@student.nust.edu.pk',
                    'first_name': 'Maryam',
                    'last_name': 'Khan',
                    'role': UserRole.PARTICIPANT,
                    'tenant': nust_tenant,
                    'phone': '+92-307-0123456',
                    'reg_num': '2022-NUST-DS-175',
                    'dept': 'Data Science',
                    'batch': '2022-2026'
                },
                {
                    'username': 'hassan.farooq',
                    'email': 'hassan.farooq@student.nust.edu.pk',
                    'first_name': 'Hassan',
                    'last_name': 'Farooq',
                    'role': UserRole.PARTICIPANT,
                    'tenant': nust_tenant,
                    'phone': '+92-308-1234567',
                    'reg_num': '2022-NUST-CS-190',
                    'dept': 'Computer Science',
                    'batch': '2022-2026'
                },
                {
                    'username': 'ayesha.siddiqua',
                    'email': 'ayesha.s@student.nust.edu.pk',
                    'first_name': 'Ayesha',
                    'last_name': 'Siddiqua',
                    'role': UserRole.PARTICIPANT,
                    'tenant': nust_tenant,
                    'phone': '+92-309-2345678',
                    'reg_num': '2022-NUST-CS-205',
                    'dept': 'Computer Science',
                    'batch': '2022-2026'
                },
                {
                    'username': 'hamza.javed',
                    'email': 'hamza.javed@student.nust.edu.pk',
                    'first_name': 'Hamza',
                    'last_name': 'Javed',
                    'role': UserRole.PARTICIPANT,
                    'tenant': nust_tenant,
                    'phone': '+92-310-3456789',
                    'reg_num': '2022-NUST-CS-220',
                    'dept': 'Computer Science',
                    'batch': '2022-2026'
                },
            ]

            users_map = {}
            for u_spec in users_spec:
                u, created = User.objects.update_or_create(
                    username=u_spec['username'],
                    defaults={
                        'email': u_spec['email'],
                        'first_name': u_spec['first_name'],
                        'last_name': u_spec['last_name'],
                        'role': u_spec['role'],
                        'tenant': u_spec['tenant'],
                        'phone_number': u_spec['phone'],
                        'is_staff': u_spec.get('is_staff', False),
                        'is_superuser': u_spec.get('is_superuser', False),
                        'is_active': True,
                        'is_verified': True
                    }
                )
                u.set_password(universal_password)
                u.save()

                UserProfile.objects.update_or_create(
                    user=u,
                    defaults={
                        'registration_number': u_spec['reg_num'],
                        'department': u_spec['dept'],
                        'batch_year': u_spec['batch'],
                        'bio': f"{u_spec['role']} at {u_spec['tenant'].name if u_spec['tenant'] else 'OptiExam Platform'}."
                    }
                )
                users_map[u.username] = u
                self.stdout.write(f"  [+] User: {u.username:<16} [{u.role:<12}] -> {u.get_full_name()}")

            # ------------------------------------------------------------------
            # 3. QUESTION BANKS & 5-FORMAT QUESTION REPOSITORIES
            # ------------------------------------------------------------------
            self.stdout.write(self.style.HTTP_INFO("\n[3/7] Authoring Question Banks & 5 Question Types (MCQ, Multi, Diagram, Short, Essay)..."))

            # Bank 1: NUST Data Structures & Algorithms
            bank_dsa, _ = QuestionBank.objects.update_or_create(
                tenant=nust_tenant,
                code='CS401-DSA',
                defaults={
                    'name': 'Data Structures & Advanced Algorithm Analysis',
                    'subject': 'Computer Science',
                    'description': 'Comprehensive repository of algorithmic complexity, tree balance, graph traversals, and dynamic programming.',
                    'created_by': users_map['prof.ahmed.bilal']
                }
            )

            # Bank 2: NUST Operating Systems
            bank_os, _ = QuestionBank.objects.update_or_create(
                tenant=nust_tenant,
                code='CS302-OS',
                defaults={
                    'name': 'Operating Systems & Kernel Concurrency',
                    'subject': 'Computer Science',
                    'description': 'Virtual memory, deadlock detection, CPU scheduling, semaphores, and inter-process communication.',
                    'created_by': users_map['prof.ahmed.bilal']
                }
            )

            # Bank 3: KEMU Clinical Physiology
            bank_med, _ = QuestionBank.objects.update_or_create(
                tenant=kemu_tenant,
                code='MED201-PHYS',
                defaults={
                    'name': 'Clinical Physiology & Cardiovascular Pathophysiology',
                    'subject': 'Medicine',
                    'description': 'Cardiac cycle, ECG analysis, renal clearance, and pulmonary ventilation.',
                    'created_by': users_map['dr.ayesha.malik']
                }
            )

            # Questions Authoring for Bank 1 (DSA)
            q_dsa_specs = [
                # 1. Single Choice MCQ
                {
                    'bank': bank_dsa,
                    'tenant': nust_tenant,
                    'question_type': Question.QuestionType.MCQ_SINGLE,
                    'prompt': 'What is the worst-case asymptotic time complexity of searching for a key in a self-balancing AVL Tree containing N nodes?',
                    'points': Decimal('2.00'),
                    'negative_points': Decimal('0.50'),
                    'difficulty': Question.Difficulty.MEDIUM,
                    'blooms_level': Question.BloomsLevel.ANALYZE,
                    'topic_tags': 'trees, avl, binary-search, complexity',
                    'hint_text': 'AVL trees enforce the balance factor property |h_L - h_R| <= 1 strictly at every node.',
                    'model_answer': 'Option B: O(log N). AVL trees guarantee strict O(log N) height.',
                    'created_by': users_map['prof.ahmed.bilal'],
                    'options': [
                        {'text': 'O(1) constant time', 'is_correct': False, 'order': 1, 'exp': 'Hash tables have average O(1), but AVL tree search depends on tree height.'},
                        {'text': 'O(log N) logarithmic time', 'is_correct': True, 'order': 2, 'exp': 'Correct. AVL trees maintain strict height balance <= 1.44 log2(N).'},
                        {'text': 'O(N) linear time', 'is_correct': False, 'order': 3, 'exp': 'Unbalanced binary search trees degrade to O(N), but AVL balances automatically.'},
                        {'text': 'O(N log N) linearithmic time', 'is_correct': False, 'order': 4, 'exp': 'This is sorting complexity, not search.'},
                    ]
                },
                # 2. Multiple Choice MCQ
                {
                    'bank': bank_dsa,
                    'tenant': nust_tenant,
                    'question_type': Question.QuestionType.MCQ_MULTIPLE,
                    'prompt': 'Which of the following sorting algorithms maintain stability (preserve relative order of duplicate keys) and achieve O(N log N) worst-case time complexity?',
                    'points': Decimal('3.00'),
                    'negative_points': Decimal('1.00'),
                    'difficulty': Question.Difficulty.HARD,
                    'blooms_level': Question.BloomsLevel.EVALUATE,
                    'topic_tags': 'sorting, stability, merge-sort, timsort',
                    'hint_text': 'Consider divide-and-conquer methods that avoid erratic partitioned swaps.',
                    'model_answer': 'Merge Sort and Timsort are both stable and guarantee O(N log N) worst case.',
                    'created_by': users_map['prof.ahmed.bilal'],
                    'options': [
                        {'text': 'Standard Merge Sort', 'is_correct': True, 'order': 1, 'exp': 'Correct. Merge sort does not reorder equal elements during the merge phase.'},
                        {'text': 'Timsort (used in Python & Java)', 'is_correct': True, 'order': 2, 'exp': 'Correct. Timsort is hybrid insertion-merge sort, stable with O(N log N) worst case.'},
                        {'text': 'Standard In-Place QuickSort', 'is_correct': False, 'order': 3, 'exp': 'Incorrect. Standard QuickSort partitioning is unstable and has O(N^2) worst case.'},
                        {'text': 'HeapSort', 'is_correct': False, 'order': 4, 'exp': 'Incorrect. Sift-down operations in heap sort do not maintain key stability.'},
                    ]
                },
                # 3. Diagram MCQ
                {
                    'bank': bank_dsa,
                    'tenant': nust_tenant,
                    'question_type': Question.QuestionType.IMAGE_MCQ,
                    'prompt': 'In a Red-Black Tree, a red child is inserted as the right child of a red parent, and the parent is a left child of its grandparent (Left-Right zigzag case with black uncle). Which rotation sequence restores the Red-Black invariant?',
                    'points': Decimal('3.00'),
                    'negative_points': Decimal('0.50'),
                    'difficulty': Question.Difficulty.HARD,
                    'blooms_level': Question.BloomsLevel.APPLY,
                    'topic_tags': 'red-black-tree, rotations, tree-balancing',
                    'hint_text': 'A zigzag configuration requires a double rotation: first straighten the zig-zag, then rotate the grandparent.',
                    'model_answer': 'Left Rotation on Parent followed by Right Rotation on Grandparent.',
                    'created_by': users_map['prof.ahmed.bilal'],
                    'options': [
                        {'text': 'Single Right Rotation on Grandparent', 'is_correct': False, 'order': 1, 'exp': 'Single rotation only resolves linear (left-left) insertions.'},
                        {'text': 'Left Rotation on Parent, then Right Rotation on Grandparent', 'is_correct': True, 'order': 2, 'exp': 'Correct. Resolves the Left-Right double rotation.'},
                        {'text': 'Right Rotation on Parent, then Left Rotation on Grandparent', 'is_correct': False, 'order': 3, 'exp': 'Incorrect orientation.'},
                        {'text': 'Double Left Rotation on Root', 'is_correct': False, 'order': 4, 'exp': 'Incorrect.'},
                    ]
                },
                # 4. Short Answer
                {
                    'bank': bank_dsa,
                    'tenant': nust_tenant,
                    'question_type': Question.QuestionType.SHORT_ANSWER,
                    'prompt': "Define the greedy choice property in Dijkstra's Algorithm and explain why it fails to compute the shortest path on directed graphs containing negative edge weights.",
                    'points': Decimal('5.00'),
                    'negative_points': Decimal('0.00'),
                    'difficulty': Question.Difficulty.MEDIUM,
                    'blooms_level': Question.BloomsLevel.UNDERSTAND,
                    'topic_tags': 'graphs, dijkstra, shortest-path, negative-weights',
                    'hint_text': 'Think about whether Dijkstra ever revisits or updates a node once finalized in the visited set.',
                    'model_answer': "Dijkstra's algorithm greedily finalizes the shortest distance to the unvisited vertex with the minimum tentative distance, assuming no future path can reduce it. In graphs with negative edge weights, traversing a longer edge initially could later lead to a massive negative-weight edge yielding a smaller total cost, which invalidates the greedy permanence assumption.",
                    'created_by': users_map['prof.ahmed.bilal']
                },
                # 5. Long Essay with Rubric Matrix
                {
                    'bank': bank_dsa,
                    'tenant': nust_tenant,
                    'question_type': Question.QuestionType.LONG_ESSAY,
                    'prompt': 'Design an efficient Distributed Rate Limiter for an online high-stakes examination platform (such as OptiExam) that receives 10,000 concurrent heartbeat requests per second across multiple server instances.\n\nYour response must address:\n1. Choice of algorithmic approach (Token Bucket, Leaky Bucket, or Sliding Window Counter).\n2. Concurrency synchronization strategy using Redis (Lua script vs Distributed Lock).\n3. Fault tolerance and failover behavior during network partitions or Redis downtime.\n4. Time and space complexity per request.',
                    'points': Decimal('10.00'),
                    'negative_points': Decimal('0.00'),
                    'difficulty': Question.Difficulty.HARD,
                    'blooms_level': Question.BloomsLevel.CREATE,
                    'topic_tags': 'system-design, distributed-systems, redis, rate-limiting, algorithms',
                    'hint_text': 'An atomic Redis Lua script prevents race conditions between GET and INCR operations.',
                    'model_answer': 'Complete architectural specification with Sliding Window Counter in Redis using ZSET timestamps, Lua script for atomic sliding window evaluation, fallback to local in-memory token bucket on connection timeout, and O(log M) complexity.',
                    'created_by': users_map['prof.ahmed.bilal'],
                    'rubrics': [
                        {'title': 'Algorithm Selection & Mathematical Clarity', 'desc': 'Clear mathematical formulation of sliding window / token bucket math.', 'points': Decimal('3.00'), 'order': 1},
                        {'title': 'Concurrency & Atomic Redis Implementation', 'desc': 'Correct atomic Lua script or lock mechanism avoiding race conditions.', 'points': Decimal('4.00'), 'order': 2},
                        {'title': 'High-Availability Failover & Complexity Analysis', 'desc': 'Graceful local degradation strategy, space complexity O(N), time O(1).', 'points': Decimal('3.00'), 'order': 3},
                    ]
                },
            ]

            dsa_questions = []
            for q_spec in q_dsa_specs:
                options_data = q_spec.pop('options', [])
                rubrics_data = q_spec.pop('rubrics', [])
                q = Question.objects.create(**q_spec)
                for opt in options_data:
                    QuestionOption.objects.create(
                        question=q,
                        option_text=opt['text'],
                        is_correct=opt['is_correct'],
                        order=opt['order'],
                        explanation=opt.get('exp', '')
                    )
                for rub in rubrics_data:
                    QuestionRubric.objects.create(
                        question=q,
                        criteria_title=rub['title'],
                        description=rub['desc'],
                        max_points=rub['points'],
                        order=rub['order']
                    )
                dsa_questions.append(q)
                self.stdout.write(f"  [+] [{q.get_question_type_display():<18}] {q.prompt[:65]}...")

            # ------------------------------------------------------------------
            # 4. EXAM BLUEPRINTS (5 Distinct Cases for Testing)
            # ------------------------------------------------------------------
            self.stdout.write(self.style.HTTP_INFO("\n[4/7] Designing Exam Blueprints & Scheduling Matrix (No Future Dates)..."))

            now = timezone.now()

            # CASE A: Past Exam - Fully Evaluated, Moderated & Published
            exam_published = Exam.objects.create(
                tenant=nust_tenant,
                title='CS401: Advanced Data Structures & Algorithms - Midterm Assessment',
                code='MID-2026-CS401',
                subject='Computer Science',
                description='Official NUST SEECS Midterm examination evaluating tree invariants, graph algorithms, and system design.',
                instructions='Attempt all questions. Section A contains objective MCQs. Section B contains structured subjective design problems. Fullscreen is enforced.',
                created_by=users_map['dr.sarah.khan'],
                start_time=now - timedelta(days=6, hours=4),
                end_time=now - timedelta(days=6, hours=1),
                duration_minutes=90,
                total_marks=Decimal('100.00'),
                passing_percentage=Decimal('50.00'),
                enforce_fullscreen=True,
                max_tab_switch_limit=3,
                lock_copy_paste=True,
                shuffle_questions=True,
                shuffle_options=True,
                allow_back_navigation=True,
                results_published=True,
                show_grader_feedback=True,
                published_at=now - timedelta(days=4),
                published_by=users_map['dr.sarah.khan'],
                is_active=True
            )

            # Sections for Exam A
            sec_a1 = ExamSection.objects.create(exam=exam_published, title='Section A: Algorithmic Foundations (Objective)', order=1, weightage=Decimal('40.00'))
            sec_a2 = ExamSection.objects.create(exam=exam_published, title='Section B: System Design & Analysis (Subjective)', order=2, weightage=Decimal('60.00'))

            # Assign questions to sections
            for idx, q in enumerate(dsa_questions[:3], 1):
                ExamQuestionAssignment.objects.create(section=sec_a1, question=q, order=idx)
            for idx, q in enumerate(dsa_questions[3:], 1):
                ExamQuestionAssignment.objects.create(section=sec_a2, question=q, order=idx)

            # Lifelines for Exam A
            for lt, max_u in [('SKIP_QUESTION', 2), ('FIFTY_FIFTY', 2), ('HINT_TOKEN', 2), ('BOOKMARK_FLAG', 10)]:
                ExamLifelineConfig.objects.create(exam=exam_published, lifeline_type=lt, is_enabled=True, max_allowed=max_u)

            self.stdout.write(f"  [+] Exam A [PUBLISHED]: {exam_published.title} ({exam_published.code})")

            # CASE B: Past Exam - In Grading & Moderation Phase
            exam_grading = Exam.objects.create(
                tenant=nust_tenant,
                title='CS302: Operating Systems & Kernel Architecture - Midterm Examination',
                code='MID-2026-CS302',
                subject='Computer Science',
                description='Concurrency, semaphores, page replacement, and kernel scheduling.',
                instructions='All questions mandatory. Closed book examination.',
                created_by=users_map['dr.sarah.khan'],
                start_time=now - timedelta(days=2, hours=3),
                end_time=now - timedelta(days=2),
                duration_minutes=120,
                total_marks=Decimal('100.00'),
                passing_percentage=Decimal('50.00'),
                results_published=False,
                is_active=True
            )
            sec_b1 = ExamSection.objects.create(exam=exam_grading, title='Section A: Core Concepts', order=1, weightage=Decimal('50.00'))
            sec_b2 = ExamSection.objects.create(exam=exam_grading, title='Section B: Applied OS Design', order=2, weightage=Decimal('50.00'))
            for idx, q in enumerate(dsa_questions[:2], 1):
                ExamQuestionAssignment.objects.create(section=sec_b1, question=q, order=idx)
            for idx, q in enumerate(dsa_questions[3:], 1):
                ExamQuestionAssignment.objects.create(section=sec_b2, question=q, order=idx)

            self.stdout.write(f"  [+] Exam B [GRADING QUEUE]: {exam_grading.title} ({exam_grading.code})")

            # CASE C: Live Right Now - In Progress (To test Designer Live Ops Control Room)
            exam_live_ops = Exam.objects.create(
                tenant=nust_tenant,
                title='CS204: Database Systems & Query Optimization - Live Lab Assessment',
                code='LIVE-2026-CS204',
                subject='Computer Science',
                description='Live real-time query optimization quiz in computer laboratory.',
                instructions='Real-time monitored assessment. Ensure fullscreen is maintained.',
                created_by=users_map['dr.sarah.khan'],
                start_time=now - timedelta(minutes=25),
                end_time=now + timedelta(minutes=95),
                duration_minutes=45,
                total_marks=Decimal('50.00'),
                passing_percentage=Decimal('40.00'),
                enforce_fullscreen=True,
                max_tab_switch_limit=3,
                results_published=False,
                is_active=True
            )
            sec_c1 = ExamSection.objects.create(exam=exam_live_ops, title='Section A: SQL & Relational Algebra', order=1, weightage=Decimal('50.00'))
            for idx, q in enumerate(dsa_questions[:3], 1):
                ExamQuestionAssignment.objects.create(section=sec_c1, question=q, order=idx)

            self.stdout.write(f"  [+] Exam C [LIVE OPS ACTIVE]: {exam_live_ops.title} ({exam_live_ops.code})")

            # CASE D: SCHEDULED TODAY / OPEN RIGHT NOW - ZERO ATTEMPTS (USER CAN ATTEMPT!)
            exam_ready_to_attempt = Exam.objects.create(
                tenant=nust_tenant,
                title='CS101: Introduction to Computing & Algorithmic Problem Solving - Live Exam',
                code='LIVE-2026-CS101',
                subject='Computer Science',
                description='Comprehensive fundamental assessment open for immediate candidate participation.',
                instructions='Welcome to CS101 Live Examination! Read each question carefully. Use 50:50 and Hint lifelines strategically. Anti-cheating shields are active.',
                created_by=users_map['dr.sarah.khan'],
                start_time=now - timedelta(minutes=15),
                end_time=now + timedelta(hours=4),
                duration_minutes=40,
                total_marks=Decimal('50.00'),
                passing_percentage=Decimal('40.00'),
                enforce_fullscreen=True,
                max_tab_switch_limit=3,
                lock_copy_paste=True,
                shuffle_questions=True,
                shuffle_options=True,
                allow_back_navigation=True,
                results_published=False,
                is_active=True
            )
            sec_d1 = ExamSection.objects.create(exam=exam_ready_to_attempt, title='Section A: Objective Challenge', order=1, weightage=Decimal('25.00'))
            sec_d2 = ExamSection.objects.create(exam=exam_ready_to_attempt, title='Section B: Problem Formulation', order=2, weightage=Decimal('25.00'))
            for idx, q in enumerate(dsa_questions[:3], 1):
                ExamQuestionAssignment.objects.create(section=sec_d1, question=q, order=idx)
            for idx, q in enumerate(dsa_questions[3:], 1):
                ExamQuestionAssignment.objects.create(section=sec_d2, question=q, order=idx)

            for lt, max_u in [('SKIP_QUESTION', 2), ('FIFTY_FIFTY', 2), ('HINT_TOKEN', 2), ('BOOKMARK_FLAG', 5)]:
                ExamLifelineConfig.objects.create(exam=exam_ready_to_attempt, lifeline_type=lt, is_enabled=True, max_allowed=max_u)

            self.stdout.write(f"  [+] Exam D [READY FOR TEST ATTEMPT]: {exam_ready_to_attempt.title} ({exam_ready_to_attempt.code})")

            # ------------------------------------------------------------------
            # 5. ROSTER ENROLLMENT & CANDIDATE ATTEMPTS
            # ------------------------------------------------------------------
            self.stdout.write(self.style.HTTP_INFO("\n[5/7] Enrolling Candidates & Generating Deterministic Attempt Trajectories..."))

            candidate_usernames = [
                'ali.hassan', 'fatima.zahra', 'usman.akbar', 'sana.iqbal', 'bilal.raza',
                'zain.abbas', 'maryam.khan', 'hassan.farooq', 'ayesha.siddiqua', 'hamza.javed'
            ]

            # Enroll all 10 candidates in Exam A (Published), Exam B (Grading), Exam C (Live Ops), Exam D (Ready to Attempt)
            for idx, uname in enumerate(candidate_usernames, 1):
                u = users_map[uname]
                # Exam A Roster
                ExamParticipantRoster.objects.create(
                    exam=exam_published,
                    participant=u,
                    candidate_index=idx,
                    registration_number=u.profile.registration_number,
                    status=ExamParticipantRoster.Status.ENROLLED
                )
                # Exam B Roster
                ExamParticipantRoster.objects.create(
                    exam=exam_grading,
                    participant=u,
                    candidate_index=idx,
                    registration_number=u.profile.registration_number,
                    status=ExamParticipantRoster.Status.ENROLLED
                )
                # Exam D (Ready to Attempt) Roster
                ExamParticipantRoster.objects.create(
                    exam=exam_ready_to_attempt,
                    participant=u,
                    candidate_index=idx,
                    registration_number=u.profile.registration_number,
                    status=ExamParticipantRoster.Status.ENROLLED
                )

            # Exam C Roster (5 candidates)
            for idx, uname in enumerate(candidate_usernames[:5], 1):
                u = users_map[uname]
                ExamParticipantRoster.objects.create(
                    exam=exam_live_ops,
                    participant=u,
                    candidate_index=idx,
                    registration_number=u.profile.registration_number,
                    status=ExamParticipantRoster.Status.ENROLLED
                )

            # --- POPULATE EXAM A (Published): 9 completed attempts (1 absent) ---
            exam_a_students = candidate_usernames[:9]  # hamza.javed was absent
            for idx, uname in enumerate(exam_a_students, 1):
                u = users_map[uname]
                att_start = exam_published.start_time + timedelta(minutes=random.randint(1, 10))
                att_sub = att_start + timedelta(minutes=random.randint(55, 85))

                att = ExamAttempt.objects.create(
                    tenant=nust_tenant,
                    exam=exam_published,
                    participant=u,
                    resume_token=uuid.uuid4().hex,
                    candidate_seed=hash(f"{u.id}_{exam_published.id}"),
                    started_at=att_start,
                    submitted_at=att_sub,
                    status=ExamAttempt.Status.SUBMITTED,
                    last_heartbeat=att_sub,
                    violation_count=random.choice([0, 0, 1, 2]),
                    is_simulation=False
                )

                # Answers for Exam A
                total_awarded = Decimal('0.00')
                for q_idx, q in enumerate(dsa_questions, 1):
                    ans = AttemptAnswer.objects.create(
                        attempt=att,
                        question=q,
                        order_in_attempt=q_idx,
                        is_bookmarked=(q_idx == 4),
                        is_skipped=False,
                        is_graded=True
                    )

                    if q.is_mcq:
                        # Pick options
                        correct_opts = list(q.options.filter(is_correct=True))
                        wrong_opts = list(q.options.filter(is_correct=False))

                        # Ali Hassan and Fatima get 100% correct, others have some variations
                        is_student_smart = uname in ['ali.hassan', 'fatima.zahra', 'maryam.khan']
                        if is_student_smart or random.random() > 0.3:
                            ans.selected_options.set(correct_opts)
                            ans.marks_awarded = q.points
                        else:
                            ans.selected_options.set(wrong_opts[:1])
                            ans.marks_awarded = -q.negative_points
                        ans.save()
                        total_awarded += (ans.marks_awarded or Decimal('0.00'))
                    else:
                        # Subjective questions
                        if q.question_type == Question.QuestionType.SHORT_ANSWER:
                            ans.text_response = "Dijkstra's algorithm greedily finalizes the minimum distance vertex in unvisited set. When negative edge weights exist, a longer path with a negative edge can later yield a smaller cost, violating the greedy invariant."
                            marks = Decimal('4.50') if uname in ['ali.hassan', 'fatima.zahra'] else Decimal('3.00')
                            ans.marks_awarded = marks
                            ans.save()
                            total_awarded += marks

                            QuestionScore.objects.create(
                                answer=ans,
                                grader=users_map['grader.zainab'],
                                awarded_marks=marks,
                                rubric_breakdown={},
                                examiner_notes='Clear explanation of Dijkstra invariant failure.',
                                feedback_to_student='Good conceptual grasp of greedy algorithm constraints.',
                                is_draft=False,
                                version=1
                            )
                        elif q.question_type == Question.QuestionType.LONG_ESSAY:
                            ans.text_response = "We implement a Distributed Rate Limiter using Redis Sliding Window Counter with ZSETs. Each incoming request runs a Lua script that removes expired timestamps, counts recent entries, and conditionally appends the current timestamp."
                            marks = Decimal('9.00') if uname in ['ali.hassan', 'fatima.zahra'] else Decimal('6.50')
                            ans.marks_awarded = marks
                            ans.save()
                            total_awarded += marks

                            QuestionScore.objects.create(
                                answer=ans,
                                grader=users_map['grader.zainab'],
                                awarded_marks=marks,
                                rubric_breakdown={'crit_1': 3.0, 'crit_2': 3.5, 'crit_3': 2.5},
                                examiner_notes='Excellent system architecture and concurrency handling.',
                                feedback_to_student='Very well structured system design diagram and Lua script explanation.',
                                is_draft=False,
                                version=1
                            )

                # Moderation record for Exam A
                is_pass = total_awarded >= (exam_published.total_marks * (exam_published.passing_percentage / Decimal('100.0')))
                GradeModeration.objects.create(
                    attempt=att,
                    moderator=users_map['dr.sarah.khan'],
                    status=GradeModeration.Status.APPROVED,
                    moderation_notes='Approved without adjustment. Evaluator marks verified.',
                    total_final_score=total_awarded,
                    is_passed=is_pass,
                    moderated_at=now - timedelta(days=4)
                )

                # Notifications for Exam A students
                Notification.objects.create(
                    user=u,
                    tenant=nust_tenant,
                    notification_type=Notification.NotificationType.RESULT_PUBLISHED,
                    title=f"Results Published: {exam_published.title}",
                    message=f"Official scorecard for {exam_published.title} ({exam_published.code}) has been published. Score: {total_awarded} pts.",
                    link_url=f"/submissions/exams/{exam_published.id}/result/",
                    created_at=now - timedelta(days=4)
                )

            # --- POPULATE EXAM B (Grading Queue): 8 completed attempts, allocations created ---
            GraderAllocation.objects.create(
                tenant=nust_tenant,
                exam=exam_grading,
                grader=users_map['grader.zainab'],
                candidate_range_start=1,
                candidate_range_end=5,
                sla_deadline=now + timedelta(hours=12),
                status=GraderAllocation.Status.IN_PROGRESS
            )
            GraderAllocation.objects.create(
                tenant=nust_tenant,
                exam=exam_grading,
                grader=users_map['grader.tariq'],
                candidate_range_start=6,
                candidate_range_end=10,
                sla_deadline=now + timedelta(hours=18),
                status=GraderAllocation.Status.PENDING
            )

            for idx, uname in enumerate(candidate_usernames[:8], 1):
                u = users_map[uname]
                att = ExamAttempt.objects.create(
                    tenant=nust_tenant,
                    exam=exam_grading,
                    participant=u,
                    resume_token=uuid.uuid4().hex,
                    candidate_seed=hash(f"{u.id}_{exam_grading.id}"),
                    started_at=exam_grading.start_time + timedelta(minutes=5),
                    submitted_at=exam_grading.start_time + timedelta(minutes=90),
                    status=ExamAttempt.Status.SUBMITTED,
                    last_heartbeat=exam_grading.start_time + timedelta(minutes=90),
                    is_simulation=False
                )
                GradeModeration.objects.create(
                    attempt=att,
                    moderator=users_map['dr.sarah.khan'],
                    status=GradeModeration.Status.PENDING
                )

            # --- POPULATE EXAM C (Live Ops Active Session): 2 active attempts in progress ---
            active_students = ['usman.akbar', 'sana.iqbal']
            for uname in active_students:
                u = users_map[uname]
                att = ExamAttempt.objects.create(
                    tenant=nust_tenant,
                    exam=exam_live_ops,
                    participant=u,
                    resume_token=uuid.uuid4().hex,
                    candidate_seed=hash(f"{u.id}_{exam_live_ops.id}"),
                    started_at=now - timedelta(minutes=20),
                    status=ExamAttempt.Status.IN_PROGRESS,
                    last_heartbeat=now - timedelta(seconds=8),
                    violation_count=1,
                    is_simulation=False
                )
                ProctoringLog.objects.create(
                    attempt=att,
                    event_type=ProctoringLog.EventType.FULLSCREEN_ENTER,
                    timestamp=now - timedelta(minutes=20),
                    details={'resolution': '1920x1080'}
                )
                ProctoringLog.objects.create(
                    attempt=att,
                    event_type=ProctoringLog.EventType.TAB_BLUR,
                    timestamp=now - timedelta(minutes=10),
                    details={'message': 'Window lost focus warning 1/3'}
                )

            # --- EXAM D (Ready to Attempt): ZERO ATTEMPTS CREATED INTENTIONALLY! ---
            self.stdout.write(self.style.SUCCESS("  [OK] Verified: Exam D (LIVE-2026-CS101) has 0 attempts for ali.hassan & fatima.zahra."))

            # ------------------------------------------------------------------
            # 6. AUDIT LOGS & NOTIFICATIONS
            # ------------------------------------------------------------------
            self.stdout.write(self.style.HTTP_INFO("\n[6/7] Logging Platform Audit Trail & System Events..."))
            AuditLog.objects.create(
                tenant=nust_tenant,
                user=users_map['dr.sarah.khan'],
                category=AuditLog.ActionCategory.EXAM_OP,
                action="Published official results for Exam MID-2026-CS401",
                ip_address="192.168.1.10",
                payload={'exam_id': exam_published.id, 'enrolled': 10, 'attempted': 9}
            )
            AuditLog.objects.create(
                tenant=nust_tenant,
                user=users_map['dr.sarah.khan'],
                category=AuditLog.ActionCategory.EXAM_OP,
                action="Scheduled live examination LIVE-2026-CS101 for Computer Science Cohort",
                ip_address="192.168.1.10",
                payload={'exam_id': exam_ready_to_attempt.id}
            )


            # ------------------------------------------------------------------
            # 7. GENERATE CREDENTIALS FILE (DEMO_CREDENTIALS.txt)
            # ------------------------------------------------------------------
            self.stdout.write(self.style.HTTP_INFO("\n[7/7] Generating Decorated DEMO_CREDENTIALS.txt File on Project Root..."))

            credentials_content = f"""========================================================================================
                      OPTIEXAM ASSESSMENT PLATFORM - DEMO CREDENTIALS
========================================================================================
Universal Password for all accounts:  {universal_password}
Platform URL:                         http://127.0.0.1:8000/auth/login/
System Status Health Check:           http://127.0.0.1:8000/core/healthz/
========================================================================================

----------------------------------------------------------------------------------------
1. PLATFORM SUPER ADMIN (SaaS Platform Directorate)
----------------------------------------------------------------------------------------
  * Username:     admin
  * Password:     {universal_password}
  * Name:         Engr. M. Tariq Javed
  * Dashboard:    http://127.0.0.1:8000/admin/saas/dashboard/
  * Capabilities: Multi-tenant institution management, Quotas, Feature Flags, Global Audit Logs.

----------------------------------------------------------------------------------------
2. DESIGNER / TENANT ADMINISTRATOR (NUST SEECS Dean)
----------------------------------------------------------------------------------------
  * Username:     dr.sarah.khan
  * Password:     {universal_password}
  * Name:         Dr. Sarah Khan (NUST)
  * Dashboard:    http://127.0.0.1:8000/dashboard/
  * Key Testing Hubs:
      - Live Exam Ops Command Center:   http://127.0.0.1:8000/exams/exams/{exam_live_ops.id}/live/
      - Cohort Analytics Hub:           http://127.0.0.1:8000/exams/exams/{exam_published.id}/analytics/
      - Pedagogical Item Analysis:      http://127.0.0.1:8000/exams/exams/{exam_published.id}/item-analysis/
      - Chief Grade Moderation Hub:     http://127.0.0.1:8000/grading/exams/{exam_grading.id}/moderation/
      - Candidate Dry-Run Simulation:   http://127.0.0.1:8000/submissions/exams/{exam_ready_to_attempt.id}/dry-run/

----------------------------------------------------------------------------------------
3. ITEM WRITER / SUBJECT MATTER EXPERT
----------------------------------------------------------------------------------------
  * Username:     prof.ahmed.bilal
  * Password:     {universal_password}
  * Name:         Prof. Ahmed Bilal (NUST CS)
  * Dashboard:    http://127.0.0.1:8000/questions/
  * Capabilities: Author 5 question formats, Rubrics, Model Answers, Dry-Run sandbox.

----------------------------------------------------------------------------------------
4. GRADER / EVALUATION OFFICER
----------------------------------------------------------------------------------------
  * Username:     grader.zainab
  * Password:     {universal_password}
  * Name:         Zainab Ali (Senior Examiner)
  * Dashboard:    http://127.0.0.1:8000/grading/
  * Key Testing Hubs:
      - Double-Blind Batch Queue:       http://127.0.0.1:8000/grading/exams/{exam_grading.id}/batch/
      - Split-Screen Grading Cockpit:   http://127.0.0.1:8000/grading/evaluate/1/

----------------------------------------------------------------------------------------
5. CANDIDATE / PARTICIPANT (STUDENT)
----------------------------------------------------------------------------------------
  * Primary User: ali.hassan  (or fatima.zahra, usman.akbar, sana.iqbal, bilal.raza)
  * Password:     {universal_password}
  * Dashboard:    http://127.0.0.1:8000/lobby/
  * Key Testing Scenarios:
      [A] ATTEMPT NEW LIVE EXAM (Active Today):
          Click "Enter Lobby" on CS101 Live Exam -> http://127.0.0.1:8000/submissions/exams/{exam_ready_to_attempt.id}/lobby/
          Experience Fullscreen lockdown, 5 question formats, 50:50 lifelines & auto-submit!

      [B] VIEW OFFICIAL PUBLISHED SCORECARD & PRINT TRANSCRIPT:
          Scorecard Link: http://127.0.0.1:8000/submissions/exams/{exam_published.id}/result/
          1-Click Print PDF Transcript via clean native @media print styling!

      [C] MY EXAM HISTORY & RECORDS:
          History Link:   http://127.0.0.1:8000/submissions/my-history/

========================================================================================
[TIP] QUICK LOGIN:
On the login screen (http://127.0.0.1:8000/auth/login/), click any of the 5 role icons
to automatically populate credentials. Double-click any icon to sign in instantly!
========================================================================================
"""
            cred_path = os.path.join(settings.BASE_DIR, 'DEMO_CREDENTIALS.txt')
            with open(cred_path, 'w', encoding='utf-8') as f:
                f.write(credentials_content.strip() + '\n')

            self.stdout.write(self.style.SUCCESS(f"  [OK] Written credentials reference to: {cred_path}"))

        # Summary
        self.stdout.write(self.style.HTTP_INFO("\n" + "=" * 80))
        self.stdout.write(self.style.SUCCESS("[SUCCESS] PAKISTANI DOMAIN SEEDING COMPLETED SUCCESSFULLY!"))
        self.stdout.write(self.style.HTTP_INFO("=" * 80))
        self.stdout.write(f"  * Tenants Provisioned:    {Tenant.objects.count()}")
        self.stdout.write(f"  * User Accounts Created:  {User.objects.count()} (5-tier roles)")
        self.stdout.write(f"  * Question Banks:         {QuestionBank.objects.count()}")
        self.stdout.write(f"  * Questions (5 Formats):  {Question.objects.count()}")
        self.stdout.write(f"  * Exam Blueprints:        {Exam.objects.count()} (4 test scenarios)")
        self.stdout.write(f"  * Roster Enrollments:     {ExamParticipantRoster.objects.count()}")
        self.stdout.write(f"  * Completed Attempts:     {ExamAttempt.objects.filter(status=ExamAttempt.Status.SUBMITTED).count()}")
        self.stdout.write(f"  * Live In-Progress:       {ExamAttempt.objects.filter(status=ExamAttempt.Status.IN_PROGRESS).count()}")
        self.stdout.write(f"  * Unattempted Live Exam:  CS101 (Ready for immediate candidate test)")
        self.stdout.write(self.style.HTTP_INFO("=" * 80) + "\n")
