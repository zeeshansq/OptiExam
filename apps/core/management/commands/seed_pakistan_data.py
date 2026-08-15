"""
Management command to seed realistic Pakistani domain data across all tables and relations.
Supports extensive question repositories (all 5 formats) and multi-section exam blueprints.
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
    help = "Seeds comprehensive, conflict-free Pakistani institutional exam data with rich multi-section exams."

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing database records before seeding.'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO("=" * 80))
        self.stdout.write(self.style.SUCCESS("  OptiExam Pakistani Domain Data Seeder & Multi-Section Engine"))
        self.stdout.write(self.style.HTTP_INFO("=" * 80))

        # 0. Automatic Schema & Migration Initialization
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
            # 1. TENANTS & INSTITUTIONAL BRANDING
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
            ned_tenant = tenants_map['ned']

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
                {
                    'username': 'engr.hamza.farooq',
                    'email': 'hamza.farooq@neduet.edu.pk',
                    'first_name': 'Engr. Hamza',
                    'last_name': 'Farooq',
                    'role': UserRole.ITEM_WRITER,
                    'tenant': ned_tenant,
                    'phone': '+92-315-7778899',
                    'reg_num': 'NED-IW-205',
                    'dept': 'Department of Electronic Engineering',
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
            # 3. QUESTION BANKS & 26+ QUESTION REPOSITORY ACROSS 5 FORMATS
            # ------------------------------------------------------------------
            self.stdout.write(self.style.HTTP_INFO("\n[3/7] Authoring Comprehensive Question Repositories (MCQ, Multi, Diagram, Short, Essay)..."))

            # Banks
            bank_dsa, _ = QuestionBank.objects.update_or_create(
                tenant=nust_tenant,
                code='CS401-DSA',
                defaults={
                    'name': 'Data Structures & Advanced Algorithm Analysis',
                    'subject': 'Computer Science',
                    'description': 'Tree balance invariants, asymptotic analysis, graph algorithms, and distributed algorithms.',
                    'created_by': users_map['prof.ahmed.bilal']
                }
            )

            bank_os, _ = QuestionBank.objects.update_or_create(
                tenant=nust_tenant,
                code='CS302-OS',
                defaults={
                    'name': 'Operating Systems & Kernel Concurrency',
                    'subject': 'Computer Science',
                    'description': 'Virtual memory, TLB mechanics, deadlock avoidance, scheduling algorithms, and IPC.',
                    'created_by': users_map['prof.ahmed.bilal']
                }
            )

            bank_prog, _ = QuestionBank.objects.update_or_create(
                tenant=nust_tenant,
                code='CS101-PROG',
                defaults={
                    'name': 'Programming Fundamentals & Systems Architecture',
                    'subject': 'Computer Science',
                    'description': 'Two\'s complement binary arithmetic, pointer semantics, recursion stack traces, and thread safety.',
                    'created_by': users_map['prof.ahmed.bilal']
                }
            )

            bank_med, _ = QuestionBank.objects.update_or_create(
                tenant=kemu_tenant,
                code='MED201-PHYS',
                defaults={
                    'name': 'Clinical Physiology & Cardiovascular Pathophysiology',
                    'subject': 'Medicine',
                    'description': 'Cardiac cycle, 12-lead ECG analysis, renal hemodynamics, and ARDS intensive care protocols.',
                    'created_by': users_map['dr.ayesha.malik']
                }
            )

            # 26 Questions Specifications (Categorized by format and bank)
            questions_catalog = [
                # --- BANK 1: CS401-DSA ---
                {
                    'id_tag': 'DSA_Q1',
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
                {
                    'id_tag': 'DSA_Q2',
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
                        {'text': 'Timsort (used in Python & Java standard libraries)', 'is_correct': True, 'order': 2, 'exp': 'Correct. Timsort is a hybrid insertion-merge sort, stable with O(N log N) worst case.'},
                        {'text': 'Standard In-Place QuickSort', 'is_correct': False, 'order': 3, 'exp': 'Incorrect. Standard QuickSort partitioning is unstable and has O(N^2) worst case.'},
                        {'text': 'HeapSort', 'is_correct': False, 'order': 4, 'exp': 'Incorrect. Sift-down operations in heap sort do not maintain key stability.'},
                    ]
                },
                {
                    'id_tag': 'DSA_Q3',
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
                {
                    'id_tag': 'DSA_Q4',
                    'bank': bank_dsa,
                    'tenant': nust_tenant,
                    'question_type': Question.QuestionType.MCQ_SINGLE,
                    'prompt': 'In open-addressing Hash Tables, which collision resolution technique specifically eliminates Primary Clustering by making probe sequences non-linear with index squared offsets?',
                    'points': Decimal('2.00'),
                    'negative_points': Decimal('0.50'),
                    'difficulty': Question.Difficulty.MEDIUM,
                    'blooms_level': Question.BloomsLevel.UNDERSTAND,
                    'topic_tags': 'hashing, open-addressing, quadratic-probing',
                    'hint_text': 'Probe offset is governed by c1*i + c2*i^2.',
                    'model_answer': 'Quadratic Probing eliminates primary clustering (long contiguous occupied blocks).',
                    'created_by': users_map['prof.ahmed.bilal'],
                    'options': [
                        {'text': 'Linear Probing', 'is_correct': False, 'order': 1, 'exp': 'Linear probing suffers severely from primary clustering.'},
                        {'text': 'Quadratic Probing', 'is_correct': True, 'order': 2, 'exp': 'Correct. Eliminates primary clustering by jumping non-linearly.'},
                        {'text': 'Separate Chaining', 'is_correct': False, 'order': 3, 'exp': 'Separate chaining uses linked lists, not open addressing.'},
                        {'text': 'Direct Addressing', 'is_correct': False, 'order': 4, 'exp': 'Direct addressing requires 1-to-1 table sizing without hashing.'},
                    ]
                },
                {
                    'id_tag': 'DSA_Q5',
                    'bank': bank_dsa,
                    'tenant': nust_tenant,
                    'question_type': Question.QuestionType.MCQ_MULTIPLE,
                    'prompt': 'Which of the following statements regarding Graph Traversal and Minimum Spanning Tree algorithms are mathematically TRUE?',
                    'points': Decimal('3.00'),
                    'negative_points': Decimal('1.00'),
                    'difficulty': Question.Difficulty.HARD,
                    'blooms_level': Question.BloomsLevel.EVALUATE,
                    'topic_tags': 'graphs, mst, kruskal, prim, tarjan',
                    'hint_text': 'Review cut properties of MSTs and Strongly Connected Components traversal.',
                    'model_answer': 'Tarjan uses single DFS for SCCs in O(V+E), and Prim with Fibonacci Heap runs in O(E + V log V).',
                    'created_by': users_map['prof.ahmed.bilal'],
                    'options': [
                        {'text': 'Tarjan\'s algorithm identifies all Strongly Connected Components in a directed graph in a single DFS pass in O(V + E).', 'is_correct': True, 'order': 1, 'exp': 'Correct. Tarjan uses lowlink values on DFS stack.'},
                        {'text': 'Prim\'s algorithm implemented with a Fibonacci Heap achieves an optimal asymptotic complexity of O(E + V log V).', 'is_correct': True, 'order': 2, 'exp': 'Correct. Decrease-key operations cost amortized O(1).'},
                        {'text': 'Kruskal\'s algorithm requires a connected graph and fails on disconnected forests.', 'is_correct': False, 'order': 3, 'exp': 'Incorrect. Kruskal naturally yields a Minimum Spanning Forest.'},
                        {'text': 'Breadth-First Search (BFS) computes single-source shortest paths on graphs with arbitrary positive and negative edge weights.', 'is_correct': False, 'order': 4, 'exp': 'Incorrect. BFS only works on unweighted graphs.'},
                    ]
                },
                {
                    'id_tag': 'DSA_Q6',
                    'bank': bank_dsa,
                    'tenant': nust_tenant,
                    'question_type': Question.QuestionType.IMAGE_MCQ,
                    'prompt': 'In a B+ Tree of order M=4 where leaf capacity is 3 keys, inserting the key 25 into an already full leaf node [10, 20, 30] triggers a node split. Which key is copied/promoted to the parent index node?',
                    'points': Decimal('3.00'),
                    'negative_points': Decimal('0.50'),
                    'difficulty': Question.Difficulty.MEDIUM,
                    'blooms_level': Question.BloomsLevel.APPLY,
                    'topic_tags': 'b-plus-tree, database-indexing, splits',
                    'hint_text': 'In B+ trees, the split point middle key is promoted to parent and retained in the right leaf child.',
                    'model_answer': 'Key 25 is promoted as the index routing discriminator.',
                    'created_by': users_map['prof.ahmed.bilal'],
                    'options': [
                        {'text': 'Key 10', 'is_correct': False, 'order': 1, 'exp': 'Incorrect.'},
                        {'text': 'Key 20', 'is_correct': False, 'order': 2, 'exp': 'Incorrect.'},
                        {'text': 'Key 25 (Middle element promoted to parent index)', 'is_correct': True, 'order': 3, 'exp': 'Correct. The median value forms the new separator index entry.'},
                        {'text': 'Key 30', 'is_correct': False, 'order': 4, 'exp': 'Incorrect.'},
                    ]
                },
                {
                    'id_tag': 'DSA_Q7',
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
                {
                    'id_tag': 'DSA_Q8',
                    'bank': bank_dsa,
                    'tenant': nust_tenant,
                    'question_type': Question.QuestionType.SHORT_ANSWER,
                    'prompt': 'Differentiate between Overlapping Subproblems and Optimal Substructure in Dynamic Programming. Provide an example of a computational problem exhibiting optimal substructure where DP is unnecessary because subproblems do not overlap.',
                    'points': Decimal('5.00'),
                    'negative_points': Decimal('0.00'),
                    'difficulty': Question.Difficulty.HARD,
                    'blooms_level': Question.BloomsLevel.ANALYZE,
                    'topic_tags': 'dynamic-programming, divide-and-conquer, optimal-substructure',
                    'hint_text': 'Binary Search and Merge Sort have optimal substructure but distinct disjoint subproblems.',
                    'model_answer': 'Optimal substructure means optimal solution of the global problem contains optimal solutions to subproblems. Overlapping subproblems means the same subproblems are solved repeatedly. Merge Sort and Binary Search exhibit optimal substructure but subproblems are strictly independent/disjoint, hence standard Divide-and-Conquer suffices without memoization.',
                    'created_by': users_map['prof.ahmed.bilal']
                },
                {
                    'id_tag': 'DSA_Q9',
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
                {
                    'id_tag': 'DSA_Q10',
                    'bank': bank_dsa,
                    'tenant': nust_tenant,
                    'question_type': Question.QuestionType.LONG_ESSAY,
                    'prompt': 'Formulate the mathematical design and concurrency safety proof for a Lock-Free Concurrent Skip List utilizing atomic Compare-And-Swap (CAS) instructions.\n\nDetail:\n1. Tower node linking and insertion protocol without global mutexes.\n2. Logical vs Physical deletion mark bits to avoid dangling pointer races.\n3. Hazard Pointers or Epoch-Based Reclamation (EBR) for safe memory deallocation.\n4. Proof of Lock-Freedom and Linearizability.',
                    'points': Decimal('10.00'),
                    'negative_points': Decimal('0.00'),
                    'difficulty': Question.Difficulty.HARD,
                    'blooms_level': Question.BloomsLevel.CREATE,
                    'topic_tags': 'concurrency, lock-free, skip-list, atomic-cas, linearizability',
                    'hint_text': 'Marking the next pointer bit identifies nodes undergoing deletion before physical unlinking.',
                    'model_answer': 'Comprehensive paper detailing Harris/Michael lock-free linked list extended to skip list towers, CAS unlinking, Hazard pointer registration per thread, and linearization points at atomic CAS steps.',
                    'created_by': users_map['prof.ahmed.bilal'],
                    'rubrics': [
                        {'title': 'Lock-Free Protocol & Tower Mechanics', 'desc': 'Accurate multi-level CAS insertion and logical mark bit deletion protocol.', 'points': Decimal('3.00'), 'order': 1},
                        {'title': 'Safe Memory Reclamation (Hazard Pointers / EBR)', 'desc': 'Complete lifecycle preventing Use-After-Free in concurrent reader threads.', 'points': Decimal('4.00'), 'order': 2},
                        {'title': 'Linearizability & Progress Guarantees', 'desc': 'Rigorous identification of linearization points and proof of lock-freedom.', 'points': Decimal('3.00'), 'order': 3},
                    ]
                },

                # --- BANK 2: CS302-OS ---
                {
                    'id_tag': 'OS_Q1',
                    'bank': bank_os,
                    'tenant': nust_tenant,
                    'question_type': Question.QuestionType.MCQ_SINGLE,
                    'prompt': 'In a Virtual Memory system with a 2-level hierarchical page table, 4 KB page size, and 48-bit virtual address space, what is the Effective Memory Access Time (EMAT) if TLB access time is 2ns, main memory access time is 50ns, and TLB hit ratio is 95%?',
                    'points': Decimal('3.00'),
                    'negative_points': Decimal('0.50'),
                    'difficulty': Question.Difficulty.MEDIUM,
                    'blooms_level': Question.BloomsLevel.APPLY,
                    'topic_tags': 'virtual-memory, tlb, emat, paging',
                    'hint_text': 'EMAT = Hit_Ratio * (t_TLB + t_Mem) + (1 - Hit_Ratio) * (t_TLB + 2*t_Mem + t_Mem).',
                    'model_answer': 'EMAT = 0.95 * (2 + 50) + 0.05 * (2 + 2*50 + 50) = 49.4 + 7.6 = 57.0 ns.',
                    'created_by': users_map['prof.ahmed.bilal'],
                    'options': [
                        {'text': '52.0 ns', 'is_correct': False, 'order': 1, 'exp': 'Calculated assuming single level page lookup.'},
                        {'text': '57.0 ns', 'is_correct': True, 'order': 2, 'exp': 'Correct. Accounts for 2 memory lookups for page tables on TLB miss plus final frame access.'},
                        {'text': '102.0 ns', 'is_correct': False, 'order': 3, 'exp': 'Incorrect.'},
                        {'text': '152.0 ns', 'is_correct': False, 'order': 4, 'exp': 'Incorrect.'},
                    ]
                },
                {
                    'id_tag': 'OS_Q2',
                    'bank': bank_os,
                    'tenant': nust_tenant,
                    'question_type': Question.QuestionType.MCQ_MULTIPLE,
                    'prompt': 'Which of the following conditions MUST hold simultaneously for a Coffman Deadlock to occur in a multiprogrammed operating system?',
                    'points': Decimal('3.00'),
                    'negative_points': Decimal('1.00'),
                    'difficulty': Question.Difficulty.MEDIUM,
                    'blooms_level': Question.BloomsLevel.REMEMBER,
                    'topic_tags': 'deadlock, coffman-conditions, synchronization',
                    'hint_text': 'All 4 conditions (Mutual Exclusion, Hold & Wait, No Preemption, Circular Wait) are necessary.',
                    'model_answer': 'Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait.',
                    'created_by': users_map['prof.ahmed.bilal'],
                    'options': [
                        {'text': 'Mutual Exclusion (At least one resource must be held in a non-shareable mode)', 'is_correct': True, 'order': 1, 'exp': 'Correct. Fundamental Coffman condition.'},
                        {'text': 'Hold and Wait (A process holding allocated resources requests additional busy resources)', 'is_correct': True, 'order': 2, 'exp': 'Correct. Fundamental Coffman condition.'},
                        {'text': 'Priority Preemption (Higher priority threads forcefully seize lower priority locks)', 'is_correct': False, 'order': 3, 'exp': 'Incorrect. Preemption eliminates deadlocks, NO preemption is required for deadlock.'},
                        {'text': 'Circular Wait (A closed chain of processes exists where each process waits for resource held by next)', 'is_correct': True, 'order': 4, 'exp': 'Correct. Fundamental Coffman condition.'},
                    ]
                },
                {
                    'id_tag': 'OS_Q3',
                    'bank': bank_os,
                    'tenant': nust_tenant,
                    'question_type': Question.QuestionType.IMAGE_MCQ,
                    'prompt': 'In a Multi-Level Feedback Queue (MLFQ) CPU Scheduler diagram, Process P1 is executing in the highest priority Queue Q0 (quantum 10ms). P1 executes for 10ms CPU burst without performing I/O. What is its transition state?',
                    'points': Decimal('3.00'),
                    'negative_points': Decimal('0.50'),
                    'difficulty': Question.Difficulty.MEDIUM,
                    'blooms_level': Question.BloomsLevel.APPLY,
                    'topic_tags': 'cpu-scheduling, mlfq, priority-queues',
                    'hint_text': 'MLFQ penalizes CPU-intensive processes by demoting them to lower priority queues with longer quantums.',
                    'model_answer': 'Demoted to lower priority Queue Q1 with a doubled quantum (e.g. 20ms).',
                    'created_by': users_map['prof.ahmed.bilal'],
                    'options': [
                        {'text': 'Remains at the head of high-priority Queue Q0', 'is_correct': False, 'order': 1, 'exp': 'Incorrect. Would cause CPU starvation of interactive processes.'},
                        {'text': 'Demoted to lower-priority Queue Q1 with an increased time quantum', 'is_correct': True, 'order': 2, 'exp': 'Correct. Standard MLFQ aging and demotion rule.'},
                        {'text': 'Terminated immediately for time quantum violation', 'is_correct': False, 'order': 3, 'exp': 'Incorrect.'},
                        {'text': 'Moved to Waiting/Blocked I/O Queue', 'is_correct': False, 'order': 4, 'exp': 'Incorrect.'},
                    ]
                },
                {
                    'id_tag': 'OS_Q4',
                    'bank': bank_os,
                    'tenant': nust_tenant,
                    'question_type': Question.QuestionType.SHORT_ANSWER,
                    'prompt': 'Explain the Priority Inversion anomaly in real-time embedded systems (such as the Mars Pathfinder incident) and describe how the Priority Inheritance Protocol prevents unbounded priority inversion.',
                    'points': Decimal('5.00'),
                    'negative_points': Decimal('0.00'),
                    'difficulty': Question.Difficulty.HARD,
                    'blooms_level': Question.BloomsLevel.UNDERSTAND,
                    'topic_tags': 'rtos, priority-inversion, priority-inheritance, mars-pathfinder',
                    'hint_text': 'A medium-priority task preempts a low-priority task holding a mutex needed by high-priority task.',
                    'model_answer': 'Priority Inversion occurs when a high-priority task H is blocked on a mutex held by low-priority task L, and medium-priority tasks M (not needing the mutex) preempt L, preventing H from executing. Under Priority Inheritance, task L temporarily inherits H\'s higher priority while holding the mutex, preventing M from preempting L until L releases the mutex.',
                    'created_by': users_map['prof.ahmed.bilal']
                },
                {
                    'id_tag': 'OS_Q5',
                    'bank': bank_os,
                    'tenant': nust_tenant,
                    'question_type': Question.QuestionType.LONG_ESSAY,
                    'prompt': 'Architect a Kernel Slab Allocator for object caching in a Unix-like operating system kernel.\n\nDetail:\n1. Data structures for `kmem_cache`, `slab_full`, `slab_partial`, and `slab_free` lists.\n2. Interaction with the underlying Buddy Page Allocator for allocating backing physical pages.\n3. Cache coloring technique to prevent L1 cache line thrashing across identical object offsets.\n4. Algorithmic trade-offs against internal and external memory fragmentation.',
                    'points': Decimal('10.00'),
                    'negative_points': Decimal('0.00'),
                    'difficulty': Question.Difficulty.HARD,
                    'blooms_level': Question.BloomsLevel.CREATE,
                    'topic_tags': 'kernel, slab-allocator, memory-management, buddy-allocator, cache-coloring',
                    'hint_text': 'Slab allocator caches initialized objects (e.g. task_struct, inode) eliminating repeat constructor overhead.',
                    'model_answer': 'Comprehensive slab allocator architecture description with kmem_cache descriptors, buddy page retrieval, freelist pointer manipulation within unallocated objects, and color offset shifting.',
                    'created_by': users_map['prof.ahmed.bilal'],
                    'rubrics': [
                        {'title': 'Slab Object Cache Architecture', 'desc': 'Precise descriptors, object constructor reuse, and partial/full list handling.', 'points': Decimal('3.00'), 'order': 1},
                        {'title': 'Buddy Page Allocator Integration & Cache Coloring', 'desc': 'Page order requests and L1 data cache coloring alignment offsets.', 'points': Decimal('4.00'), 'order': 2},
                        {'title': 'Fragmentation Mitigation & Free List Efficiency', 'desc': 'Complete analysis of internal fragmentation elimination and O(1) object reuse.', 'points': Decimal('3.00'), 'order': 3},
                    ]
                },

                # --- BANK 3: CS101-PROG ---
                {
                    'id_tag': 'PROG_Q1',
                    'bank': bank_prog,
                    'tenant': nust_tenant,
                    'question_type': Question.QuestionType.MCQ_SINGLE,
                    'prompt': 'In 8-bit Two\'s Complement signed integer representation, what is the resulting decimal integer value of computing `(~(0b00110101) + 1)`?',
                    'points': Decimal('2.00'),
                    'negative_points': Decimal('0.50'),
                    'difficulty': Question.Difficulty.EASY,
                    'blooms_level': Question.BloomsLevel.APPLY,
                    'topic_tags': 'binary, arithmetic, two-complement, bitwise',
                    'hint_text': '0b00110101 = 53 in decimal. Two\'s complement negation yields -X.',
                    'model_answer': '-53 in decimal.',
                    'created_by': users_map['prof.ahmed.bilal'],
                    'options': [
                        {'text': '+53', 'is_correct': False, 'order': 1, 'exp': 'Incorrect sign.'},
                        {'text': '-53', 'is_correct': True, 'order': 2, 'exp': 'Correct. Bitwise inversion plus 1 computes the arithmetic negation.'},
                        {'text': '-54', 'is_correct': False, 'order': 3, 'exp': 'This would be just bitwise inversion (~X).'},
                        {'text': '-203', 'is_correct': False, 'order': 4, 'exp': 'Unsigned interpretation.'},
                    ]
                },
                {
                    'id_tag': 'PROG_Q2',
                    'bank': bank_prog,
                    'tenant': nust_tenant,
                    'question_type': Question.QuestionType.MCQ_MULTIPLE,
                    'prompt': 'Which of the following statements correctly describe pass-by-value versus pass-by-reference semantics across C++ and Python?',
                    'points': Decimal('3.00'),
                    'negative_points': Decimal('1.00'),
                    'difficulty': Question.Difficulty.MEDIUM,
                    'blooms_level': Question.BloomsLevel.UNDERSTAND,
                    'topic_tags': 'pointers, references, python-memory, cpp-semantics',
                    'hint_text': 'Python uses "pass-by-assignment" / "pass-by-object-reference".',
                    'model_answer': 'In C++, modifying a `Type&` modifies the original variable; in Python, reassigning a parameter binds a new object.',
                    'created_by': users_map['prof.ahmed.bilal'],
                    'options': [
                        {'text': 'In C++, passing by reference (`void fn(int& x)`) allows direct mutation of the caller\'s original stack variable.', 'is_correct': True, 'order': 1, 'exp': 'Correct. C++ references are aliases for the caller variable.'},
                        {'text': 'In Python, variables are object references; mutating a mutable object (like a list) inside a function reflects in caller scope.', 'is_correct': True, 'order': 2, 'exp': 'Correct. In-place mutations modify the underlying heap object.'},
                        {'text': 'Reassigning a parameter `x = [1, 2]` inside a Python function automatically overwrites the caller\'s list reference.', 'is_correct': False, 'order': 3, 'exp': 'Incorrect. Reassignment only changes local scope variable binding.'},
                        {'text': 'Passing large structs by value in C++ avoids memory copies on the stack.', 'is_correct': False, 'order': 4, 'exp': 'Incorrect. Pass-by-value invokes the copy constructor.'},
                    ]
                },
                {
                    'id_tag': 'PROG_Q3',
                    'bank': bank_prog,
                    'tenant': nust_tenant,
                    'question_type': Question.QuestionType.IMAGE_MCQ,
                    'prompt': 'Consider the recursive function execution `int fib(int n) { if (n <= 1) return n; return fib(n-1) + fib(n-2); }`. For the call `fib(4)`, what is the maximum depth of the call stack frames simultaneously active in memory?',
                    'points': Decimal('3.00'),
                    'negative_points': Decimal('0.50'),
                    'difficulty': Question.Difficulty.MEDIUM,
                    'blooms_level': Question.BloomsLevel.ANALYZE,
                    'topic_tags': 'recursion, call-stack, activation-records',
                    'hint_text': 'Stack depth equals the height of the recursion tree from root to deepest leaf.',
                    'model_answer': 'Maximum stack depth is 4 (calls: fib(4) -> fib(3) -> fib(2) -> fib(1)).',
                    'created_by': users_map['prof.ahmed.bilal'],
                    'options': [
                        {'text': '2 frames', 'is_correct': False, 'order': 1, 'exp': 'Incorrect.'},
                        {'text': '4 frames (Height of recursive call chain)', 'is_correct': True, 'order': 2, 'exp': 'Correct. Active frames: fib(4) -> fib(3) -> fib(2) -> fib(1).'},
                        {'text': '9 frames', 'is_correct': False, 'order': 3, 'exp': 'This is total calls, not simultaneous stack depth.'},
                        {'text': '16 frames', 'is_correct': False, 'order': 4, 'exp': 'Incorrect.'},
                    ]
                },
                {
                    'id_tag': 'PROG_Q4',
                    'bank': bank_prog,
                    'tenant': nust_tenant,
                    'question_type': Question.QuestionType.SHORT_ANSWER,
                    'prompt': 'Explain Tail Call Optimization (TCO). How does a compiler eliminate stack frame growth for tail-recursive functions, and why is standard Python not configured with automatic TCO?',
                    'points': Decimal('4.00'),
                    'negative_points': Decimal('0.00'),
                    'difficulty': Question.Difficulty.MEDIUM,
                    'blooms_level': Question.BloomsLevel.UNDERSTAND,
                    'topic_tags': 'recursion, tail-call, compiler-optimization',
                    'hint_text': 'When recursive call is the final statement, compiler overwrites the current stack frame with a jump instruction.',
                    'model_answer': 'In tail call optimization, when a subroutine call is the final action in a function, the compiler reuses the current activation record instead of pushing a new frame, transforming recursion into an O(1) space iterative loop. Python intentionally omits TCO to preserve full stack tracebacks for debugging and inspection.',
                    'created_by': users_map['prof.ahmed.bilal']
                },
                {
                    'id_tag': 'PROG_Q5',
                    'bank': bank_prog,
                    'tenant': nust_tenant,
                    'question_type': Question.QuestionType.LONG_ESSAY,
                    'prompt': 'Implement a Thread-Safe Bounded Circular Ring Buffer (Producer-Consumer Queue) in Python/C++.\n\nYour submission must:\n1. Handle index wrap-around using modulo arithmetic or power-of-two bitwise masking.\n2. Implement concurrency synchronization using Mutex Locks and Condition Variables (`not_full`, `not_empty`).\n3. Address cache false sharing prevention using cache-line padding between head and tail atomic pointers.\n4. Provide throughput benchmarking and edge case handling during buffer exhaustion.',
                    'points': Decimal('8.00'),
                    'negative_points': Decimal('0.00'),
                    'difficulty': Question.Difficulty.HARD,
                    'blooms_level': Question.BloomsLevel.CREATE,
                    'topic_tags': 'concurrency, ring-buffer, producer-consumer, condition-variables, false-sharing',
                    'hint_text': 'Condition variables must wait inside a `while` loop to protect against spurious wakeups.',
                    'model_answer': 'Complete thread-safe ring buffer code with robust condition variable wait loops, atomic indices, 64-byte hardware cacheline padding, and O(1) push/pop complexity.',
                    'created_by': users_map['prof.ahmed.bilal'],
                    'rubrics': [
                        {'title': 'Ring Buffer Index Math & Buffer Bounds', 'desc': 'Accurate circular modulo logic and empty/full invariant preservation.', 'points': Decimal('2.00'), 'order': 1},
                        {'title': 'Thread Synchronization & Spurious Wakeups', 'desc': 'Correct condition variable loops and lock release safety.', 'points': Decimal('3.00'), 'order': 2},
                        {'title': 'Cache Line Padding & False Sharing Defense', 'desc': 'Hardware-aware 64-byte alignas padding between producer and consumer pointers.', 'points': Decimal('3.00'), 'order': 3},
                    ]
                },

                # --- BANK 4: MED201-PHYS (KEMU) ---
                {
                    'id_tag': 'MED_Q1',
                    'bank': bank_med,
                    'tenant': kemu_tenant,
                    'question_type': Question.QuestionType.MCQ_SINGLE,
                    'prompt': 'According to the Frank-Starling Law of the Heart, what physiological parameter directly determines the force of ventricular contraction during systole?',
                    'points': Decimal('2.00'),
                    'negative_points': Decimal('0.50'),
                    'difficulty': Question.Difficulty.MEDIUM,
                    'blooms_level': Question.BloomsLevel.UNDERSTAND,
                    'topic_tags': 'cardiology, physiology, frank-starling, preload',
                    'hint_text': 'Initial stretching of cardiac myocyte sarcomeres is proportional to End-Diastolic Volume.',
                    'model_answer': 'End-Diastolic Volume (Preload) directly determines the initial stretch and contractility.',
                    'created_by': users_map['dr.ayesha.malik'],
                    'options': [
                        {'text': 'Systemic Vascular Resistance (Afterload)', 'is_correct': False, 'order': 1, 'exp': 'Afterload opposes ejection.'},
                        {'text': 'End-Diastolic Ventricular Volume / Sarcomere Stretch (Preload)', 'is_correct': True, 'order': 2, 'exp': 'Correct. Increased venous return stretches myocytes to optimal actin-myosin overlap.'},
                        {'text': 'Sympathetic Beta-1 Adrenergic Tone alone', 'is_correct': False, 'order': 3, 'exp': 'Inotropic tone alters Starling curve, but law describes intrinsic stretch mechanism.'},
                        {'text': 'Pulmonary Capillary Wedge Pressure alone', 'is_correct': False, 'order': 4, 'exp': 'Indirect marker of left atrial pressure.'},
                    ]
                },
                {
                    'id_tag': 'MED_Q2',
                    'bank': bank_med,
                    'tenant': kemu_tenant,
                    'question_type': Question.QuestionType.IMAGE_MCQ,
                    'prompt': 'A 58-year-old patient presents with acute substernal chest pressure. The 12-Lead ECG demonstrates marked ST-Segment Elevations in Leads II, III, and aVF with reciprocal ST-depressions in Leads I and aVL. Which coronary artery is occluded?',
                    'points': Decimal('3.00'),
                    'negative_points': Decimal('0.50'),
                    'difficulty': Question.Difficulty.HARD,
                    'blooms_level': Question.BloomsLevel.APPLY,
                    'topic_tags': 'cardiology, ecg, stemi, myocardial-infarction',
                    'hint_text': 'Leads II, III, aVF view the inferior myocardial wall, supplied predominantly by RCA.',
                    'model_answer': 'Right Coronary Artery (RCA) causing an Acute Inferior Wall STEMI.',
                    'created_by': users_map['dr.ayesha.malik'],
                    'options': [
                        {'text': 'Left Anterior Descending Artery (LAD)', 'is_correct': False, 'order': 1, 'exp': 'LAD occlusion causes anterior STEMI (V1-V4).'},
                        {'text': 'Right Coronary Artery (RCA) - Inferior Myocardial Infarction', 'is_correct': True, 'order': 2, 'exp': 'Correct. Leads II, III, aVF record inferior wall vector supplied by RCA in 85% of individuals.'},
                        {'text': 'Left Circumflex Artery (LCx) - Lateral Infarction', 'is_correct': False, 'order': 3, 'exp': 'LCx causes lateral STEMI (I, aVL, V5, V6).'},
                        {'text': 'Left Main Coronary Artery Trunk', 'is_correct': False, 'order': 4, 'exp': 'Left main causes diffuse ischemic depressions with aVR elevation.'},
                    ]
                },
                {
                    'id_tag': 'MED_Q3',
                    'bank': bank_med,
                    'tenant': kemu_tenant,
                    'question_type': Question.QuestionType.SHORT_ANSWER,
                    'prompt': 'Detail the physiological cascade of the Renin-Angiotensin-Aldosterone System (RAAS) initiated by juxtaglomerular macula densa sensing of decreased sodium chloride delivery, and its impact on glomerular filtration rate (GFR).',
                    'points': Decimal('5.00'),
                    'negative_points': Decimal('0.00'),
                    'difficulty': Question.Difficulty.HARD,
                    'blooms_level': Question.BloomsLevel.UNDERSTAND,
                    'topic_tags': 'renal, physiology, raas, gfr, aldosterone',
                    'hint_text': 'Renin converts angiotensinogen to Ang I; ACE converts Ang I to Ang II; Ang II selectively constricts efferent arterioles.',
                    'model_answer': 'Macula densa senses low NaCl -> Juxtaglomerular cells release Renin -> Renin cleaves hepatic Angiotensinogen to Angiotensin I -> Pulmonary Endothelial ACE converts Ang I to Angiotensin II -> Ang II preferentially constricts the renal Efferent Arteriole, increasing glomerular hydrostatic pressure to maintain GFR despite systemic hypotension. Ang II also triggers Aldosterone release from adrenal cortex promoting distal tubule sodium and water reabsorption.',
                    'created_by': users_map['dr.ayesha.malik']
                },
                {
                    'id_tag': 'MED_Q4',
                    'bank': bank_med,
                    'tenant': kemu_tenant,
                    'question_type': Question.QuestionType.LONG_ESSAY,
                    'prompt': 'Formulate the clinical pathophysiology, diagnostic criteria (Berlin Definition), and lung-protective mechanical ventilation protocol for Acute Respiratory Distress Syndrome (ARDS) in an Intensive Care Unit.\n\nDetail:\n1. Diffuse Alveolar Damage stages (Exudative, Proliferative, Fibrotic) and surfactant loss.\n2. Berlin criteria (PaO2/FiO2 ratio stratification, non-cardiogenic origin).\n3. ARDSNet low tidal volume ventilation protocol (6 mL/kg ideal body weight, plateau pressure <= 30 cm H2O, PEEP titration, prone positioning).',
                    'points': Decimal('10.00'),
                    'negative_points': Decimal('0.00'),
                    'difficulty': Question.Difficulty.HARD,
                    'blooms_level': Question.BloomsLevel.CREATE,
                    'topic_tags': 'intensive-care, ards, ventilation, physiology, berlin-definition',
                    'hint_text': 'ARDSNet protocol strictly caps tidal volume at 6 mL/kg PBW to prevent volutrauma and barotrauma.',
                    'model_answer': 'Complete clinical essay detailing capillary endothelial injury, hyaline membrane formation, PaO2/FiO2 ratio classification (Mild 200-300, Moderate 100-200, Severe <100), low tidal volume strategy, and neuromuscular blockade with prone positioning.',
                    'created_by': users_map['dr.ayesha.malik'],
                    'rubrics': [
                        {'title': 'Pathophysiological Progression & Surfactant Dynamics', 'desc': 'Exudative phase, hyaline membranes, and V/Q mismatching.', 'points': Decimal('3.00'), 'order': 1},
                        {'title': 'Berlin Diagnostic Criteria & Severity Grading', 'desc': 'Accurate timing, bilateral opacities, and PaO2/FiO2 ratio cutoffs.', 'points': Decimal('3.00'), 'order': 2},
                        {'title': 'Evidence-Based ARDSNet Ventilation Strategy', 'desc': '6 mL/kg PBW, driving pressure optimization, PEEP titration, and prone positioning.', 'points': Decimal('4.00'), 'order': 3},
                    ]
                },
            ]

            q_map = {}
            for q_spec in questions_catalog:
                id_tag = q_spec.pop('id_tag')
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
                q_map[id_tag] = q
                self.stdout.write(f"  [+] [{q.get_question_type_display():<18}] {q.prompt[:60]}... ({q.points} pts)")

            # ------------------------------------------------------------------
            # 4. EXAM BLUEPRINTS & RICH MULTI-SECTION ARCHITECTURES
            # ------------------------------------------------------------------
            self.stdout.write(self.style.HTTP_INFO("\n[4/7] Designing Multi-Section Exam Blueprints & Scheduling Matrix..."))

            now = timezone.now()

            # Helper for adding question assignments
            def assign_questions(section, question_tags):
                for idx, tag in enumerate(question_tags, 1):
                    ExamQuestionAssignment.objects.create(
                        section=section,
                        question=q_map[tag],
                        order=idx
                    )

            # ── EXAM 1: CS401 (Published & Fully Graded Midterm) ─────────────
            exam_published = Exam.objects.create(
                tenant=nust_tenant,
                title='CS401: Advanced Data Structures & Algorithms - Midterm Assessment',
                code='MID-2026-CS401',
                subject='Computer Science',
                description='Official NUST SEECS Midterm examination evaluating tree invariants, graph algorithms, and system design.',
                instructions='Attempt all questions across all 4 sections. Section A & B are objective MCQs. Section C & D require detailed technical proofs and system designs. Fullscreen lockdown is strictly enforced.',
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
            # 4 Sections for Exam 1
            sec_e1_s1 = ExamSection.objects.create(exam=exam_published, title='Section A: Algorithmic Invariants & Search (Single MCQs)', order=1, weightage=Decimal('25.00'))
            sec_e1_s2 = ExamSection.objects.create(exam=exam_published, title='Section B: Visual Trees, Sorting & Graphs (Multi & Diagram MCQs)', order=2, weightage=Decimal('35.00'))
            sec_e1_s3 = ExamSection.objects.create(exam=exam_published, title='Section C: Algorithmic Mechanics & Theoretical Proofs (Short Answers)', order=3, weightage=Decimal('20.00'))
            sec_e1_s4 = ExamSection.objects.create(exam=exam_published, title='Section D: Scalable System Architecture & Concurrent Design (Long Essay)', order=4, weightage=Decimal('20.00'))

            assign_questions(sec_e1_s1, ['DSA_Q1', 'DSA_Q4', 'OS_Q1'])
            assign_questions(sec_e1_s2, ['DSA_Q2', 'DSA_Q3', 'DSA_Q5', 'DSA_Q6'])
            assign_questions(sec_e1_s3, ['DSA_Q7', 'DSA_Q8'])
            assign_questions(sec_e1_s4, ['DSA_Q9', 'DSA_Q10'])

            for lt, max_u in [('SKIP_QUESTION', 2), ('FIFTY_FIFTY', 2), ('HINT_TOKEN', 2), ('BOOKMARK_FLAG', 10)]:
                ExamLifelineConfig.objects.create(exam=exam_published, lifeline_type=lt, is_enabled=True, max_allowed=max_u)
            self.stdout.write(f"  [+] Exam 1 [PUBLISHED]: {exam_published.title} ({exam_published.sections.count()} Sections, {exam_published.total_assigned_questions} Questions)")

            # ── EXAM 2: CS302 (Grading Queue & Chief Examiner Moderation) ─────
            exam_grading = Exam.objects.create(
                tenant=nust_tenant,
                title='CS302: Operating Systems & Kernel Architecture - Midterm Examination',
                code='MID-2026-CS302',
                subject='Computer Science',
                description='Concurrency, semaphores, page replacement, TLB math, and kernel memory allocators.',
                instructions='All questions mandatory across 4 sections. Closed book examination. Ensure detailed diagrams for kernel allocator design.',
                created_by=users_map['dr.sarah.khan'],
                start_time=now - timedelta(days=2, hours=3),
                end_time=now - timedelta(days=2),
                duration_minutes=120,
                total_marks=Decimal('100.00'),
                passing_percentage=Decimal('50.00'),
                results_published=False,
                is_active=True
            )
            # 4 Sections for Exam 2
            sec_e2_s1 = ExamSection.objects.create(exam=exam_grading, title='Section A: Virtual Memory & Address Translation (MCQs)', order=1, weightage=Decimal('25.00'))
            sec_e2_s2 = ExamSection.objects.create(exam=exam_grading, title='Section B: Concurrency, Deadlock & Scheduling Diagnostics', order=2, weightage=Decimal('30.00'))
            sec_e2_s3 = ExamSection.objects.create(exam=exam_grading, title='Section C: OS Kernel Mechanisms & Real-Time Anomalies (Short Answers)', order=3, weightage=Decimal('20.00'))
            sec_e2_s4 = ExamSection.objects.create(exam=exam_grading, title='Section D: Kernel Memory Allocator Architecture (Long Essay)', order=4, weightage=Decimal('25.00'))

            assign_questions(sec_e2_s1, ['OS_Q1', 'PROG_Q1', 'DSA_Q4'])
            assign_questions(sec_e2_s2, ['OS_Q2', 'OS_Q3', 'PROG_Q2'])
            assign_questions(sec_e2_s3, ['OS_Q4', 'PROG_Q4'])
            assign_questions(sec_e2_s4, ['OS_Q5'])

            self.stdout.write(f"  [+] Exam 2 [GRADING QUEUE]: {exam_grading.title} ({exam_grading.sections.count()} Sections, {exam_grading.total_assigned_questions} Questions)")

            # ── EXAM 3: CS204 (Live Ops Active Session) ──────────────────────
            exam_live_ops = Exam.objects.create(
                tenant=nust_tenant,
                title='CS204: Database Systems & Query Optimization - Live Lab Assessment',
                code='LIVE-2026-CS204',
                subject='Computer Science',
                description='Live real-time monitored lab quiz on indexing, tree splits, and recursion performance.',
                instructions='Monitored assessment. Anti-cheat shield active. Maintain fullscreen at all times.',
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
            # 3 Sections for Exam 3
            sec_e3_s1 = ExamSection.objects.create(exam=exam_live_ops, title='Section A: Algorithmic & Bitwise Fundamentals', order=1, weightage=Decimal('30.00'))
            sec_e3_s2 = ExamSection.objects.create(exam=exam_live_ops, title='Section B: Tree Split Invariants & Call Traces (Diagrams)', order=2, weightage=Decimal('40.00'))
            sec_e3_s3 = ExamSection.objects.create(exam=exam_live_ops, title='Section C: Subproblem Formulation (Short Answer)', order=3, weightage=Decimal('30.00'))

            assign_questions(sec_e3_s1, ['DSA_Q1', 'PROG_Q1'])
            assign_questions(sec_e3_s2, ['DSA_Q6', 'PROG_Q3', 'DSA_Q2'])
            assign_questions(sec_e3_s3, ['DSA_Q8'])

            self.stdout.write(f"  [+] Exam 3 [LIVE OPS ACTIVE]: {exam_live_ops.title} ({exam_live_ops.sections.count()} Sections, {exam_live_ops.total_assigned_questions} Questions)")

            # ── EXAM 4: CS101 (READY FOR CANDIDATE TO ATTEMPT TODAY!) ─────────
            exam_ready_to_attempt = Exam.objects.create(
                tenant=nust_tenant,
                title='CS101: Introduction to Computing & Algorithmic Problem Solving - Live Exam',
                code='LIVE-2026-CS101',
                subject='Computer Science',
                description='Comprehensive fundamental assessment open for immediate candidate participation with 4 rich sections.',
                instructions='Welcome to CS101 Live Examination! Read each question carefully. Section A & B are objective questions. Section C & D test conceptual explanations and concurrency implementation. Lifelines (50:50 and Hint) are active.',
                created_by=users_map['dr.sarah.khan'],
                start_time=now - timedelta(minutes=15),
                end_time=now + timedelta(hours=4),
                duration_minutes=50,
                total_marks=Decimal('60.00'),
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
            # 4 Sections for Exam 4 (Rich variety of question types!)
            sec_e4_s1 = ExamSection.objects.create(exam=exam_ready_to_attempt, title='Section A: Fundamental Computational Logic (Single MCQs)', order=1, weightage=Decimal('25.00'))
            sec_e4_s2 = ExamSection.objects.create(exam=exam_ready_to_attempt, title='Section B: Diagrammatic Traces & Multi-Choice Analysis', order=2, weightage=Decimal('35.00'))
            sec_e4_s3 = ExamSection.objects.create(exam=exam_ready_to_attempt, title='Section C: Algorithmic Mechanics & Optimization (Short Answers)', order=3, weightage=Decimal('20.00'))
            sec_e4_s4 = ExamSection.objects.create(exam=exam_ready_to_attempt, title='Section D: Concurrent Ring Buffer Implementation (Long Essay)', order=4, weightage=Decimal('20.00'))

            assign_questions(sec_e4_s1, ['PROG_Q1', 'DSA_Q1', 'DSA_Q4'])
            assign_questions(sec_e4_s2, ['PROG_Q2', 'PROG_Q3', 'DSA_Q2', 'DSA_Q3'])
            assign_questions(sec_e4_s3, ['PROG_Q4', 'DSA_Q7'])
            assign_questions(sec_e4_s4, ['PROG_Q5'])

            for lt, max_u in [('SKIP_QUESTION', 2), ('FIFTY_FIFTY', 2), ('HINT_TOKEN', 2), ('BOOKMARK_FLAG', 5)]:
                ExamLifelineConfig.objects.create(exam=exam_ready_to_attempt, lifeline_type=lt, is_enabled=True, max_allowed=max_u)

            self.stdout.write(f"  [+] Exam 4 [READY FOR TEST ATTEMPT]: {exam_ready_to_attempt.title} ({exam_ready_to_attempt.sections.count()} Sections, {exam_ready_to_attempt.total_assigned_questions} Questions)")

            # ── EXAM 5: KEMU Clinical Physiology Spotter Exam ────────────────
            exam_kemu = Exam.objects.create(
                tenant=kemu_tenant,
                title='MED201: Clinical Physiology & Emergency Cardiology - Spotter Exam',
                code='MED-2026-MED201',
                subject='Medicine',
                description='Cardiovascular vector analysis, hemodynamics, and ARDS critical care management.',
                instructions='Strict medical assessment protocol.',
                created_by=users_map['dr.khalid.mahmood'],
                start_time=now - timedelta(days=1, hours=2),
                end_time=now - timedelta(days=1),
                duration_minutes=60,
                total_marks=Decimal('50.00'),
                passing_percentage=Decimal('50.00'),
                results_published=False,
                is_active=True
            )
            sec_e5_s1 = ExamSection.objects.create(exam=exam_kemu, title='Section A: Cardiovascular Electrophysiology & Spotter MCQs', order=1, weightage=Decimal('30.00'))
            sec_e5_s2 = ExamSection.objects.create(exam=exam_kemu, title='Section B: Neurohormonal & Renal Mechanisms (Short Conceptual)', order=2, weightage=Decimal('30.00'))
            sec_e5_s3 = ExamSection.objects.create(exam=exam_kemu, title='Section C: Critical Care Differential Diagnosis & Management (Long Essay)', order=3, weightage=Decimal('40.00'))

            assign_questions(sec_e5_s1, ['MED_Q1', 'MED_Q2'])
            assign_questions(sec_e5_s2, ['MED_Q3'])
            assign_questions(sec_e5_s3, ['MED_Q4'])

            self.stdout.write(f"  [+] Exam 5 [KEMU MEDICAL]: {exam_kemu.title} ({exam_kemu.sections.count()} Sections, {exam_kemu.total_assigned_questions} Questions)")

            # ------------------------------------------------------------------
            # 5. ROSTER ENROLLMENT & DETERMINISTIC STUDENT ATTEMPTS
            # ------------------------------------------------------------------
            self.stdout.write(self.style.HTTP_INFO("\n[5/7] Enrolling Candidates & Generating Comprehensive Attempt Responses..."))

            candidate_usernames = [
                'ali.hassan', 'fatima.zahra', 'usman.akbar', 'sana.iqbal', 'bilal.raza',
                'zain.abbas', 'maryam.khan', 'hassan.farooq', 'ayesha.siddiqua', 'hamza.javed'
            ]

            # Enroll all 10 candidates in NUST Exams (A, B, C, D)
            for idx, uname in enumerate(candidate_usernames, 1):
                u = users_map[uname]
                ExamParticipantRoster.objects.create(
                    exam=exam_published, participant=u, candidate_index=idx,
                    registration_number=u.profile.registration_number, status=ExamParticipantRoster.Status.ENROLLED
                )
                ExamParticipantRoster.objects.create(
                    exam=exam_grading, participant=u, candidate_index=idx,
                    registration_number=u.profile.registration_number, status=ExamParticipantRoster.Status.ENROLLED
                )
                ExamParticipantRoster.objects.create(
                    exam=exam_ready_to_attempt, participant=u, candidate_index=idx,
                    registration_number=u.profile.registration_number, status=ExamParticipantRoster.Status.ENROLLED
                )

            # Exam C Roster (5 candidates)
            for idx, uname in enumerate(candidate_usernames[:5], 1):
                u = users_map[uname]
                ExamParticipantRoster.objects.create(
                    exam=exam_live_ops, participant=u, candidate_index=idx,
                    registration_number=u.profile.registration_number, status=ExamParticipantRoster.Status.ENROLLED
                )

            # ── POPULATE COMPLETED ATTEMPTS FOR EXAM 1 (Published) ─────────────
            exam1_questions = [
                a.question for a in ExamQuestionAssignment.objects.filter(section__exam=exam_published).select_related('question').order_by('section__order', 'order')
            ]
            exam1_students = candidate_usernames[:9]  # 9 completed, 1 absent

            for idx, uname in enumerate(exam1_students, 1):
                u = users_map[uname]
                att_start = exam_published.start_time + timedelta(minutes=random.randint(1, 10))
                att_sub = att_start + timedelta(minutes=random.randint(65, 88))

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

                total_awarded = Decimal('0.00')
                is_student_smart = uname in ['ali.hassan', 'fatima.zahra', 'maryam.khan']

                for q_idx, q in enumerate(exam1_questions, 1):
                    ans = AttemptAnswer.objects.create(
                        attempt=att,
                        question=q,
                        order_in_attempt=q_idx,
                        is_bookmarked=(q_idx in [3, 7]),
                        is_skipped=False,
                        is_graded=True
                    )

                    if q.is_mcq:
                        correct_opts = list(q.options.filter(is_correct=True))
                        wrong_opts = list(q.options.filter(is_correct=False))

                        if is_student_smart or random.random() > 0.25:
                            ans.selected_options.set(correct_opts)
                            ans.marks_awarded = q.points
                        else:
                            ans.selected_options.set(wrong_opts[:1])
                            ans.marks_awarded = -q.negative_points
                        ans.save()
                        total_awarded += (ans.marks_awarded or Decimal('0.00'))

                    elif q.question_type == Question.QuestionType.SHORT_ANSWER:
                        ans.text_response = f"Detailed conceptual response for {q.prompt[:40]}... The fundamental invariant is strictly preserved via optimal recurrence formulation."
                        marks = q.points * (Decimal('0.90') if is_student_smart else Decimal('0.65'))
                        ans.marks_awarded = marks
                        ans.save()
                        total_awarded += marks

                        QuestionScore.objects.create(
                            answer=ans,
                            grader=users_map['grader.zainab'],
                            awarded_marks=marks,
                            rubric_breakdown={},
                            examiner_notes='Accurate conceptual explanation with clear reasoning.',
                            feedback_to_student='Well-formulated explanation.',
                            is_draft=False,
                            version=1
                        )

                    elif q.question_type == Question.QuestionType.LONG_ESSAY:
                        ans.text_response = f"Comprehensive architectural blueprint addressing {q.prompt[:50]}...\n1. Core mathematical modeling.\n2. Concurrency synchronization using atomic primitives.\n3. Failover mitigation."
                        marks = q.points * (Decimal('0.88') if is_student_smart else Decimal('0.60'))
                        ans.marks_awarded = marks
                        ans.save()
                        total_awarded += marks

                        QuestionScore.objects.create(
                            answer=ans,
                            grader=users_map['grader.zainab'],
                            awarded_marks=marks,
                            rubric_breakdown={'crit_1': float(marks * Decimal('0.35')), 'crit_2': float(marks * Decimal('0.40')), 'crit_3': float(marks * Decimal('0.25'))},
                            examiner_notes='Excellent system architecture design with clear concurrency handling.',
                            feedback_to_student='Very well structured system design diagram and explanation.',
                            is_draft=False,
                            version=1
                        )

                # Moderation
                is_pass = total_awarded >= (exam_published.total_marks * (exam_published.passing_percentage / Decimal('100.0')))
                GradeModeration.objects.create(
                    attempt=att,
                    moderator=users_map['dr.sarah.khan'],
                    status=GradeModeration.Status.APPROVED,
                    moderation_notes='Approved without adjustment. Evaluator marks verified across all 4 sections.',
                    total_final_score=total_awarded,
                    is_passed=is_pass,
                    moderated_at=now - timedelta(days=4)
                )

                # In-App Notification
                Notification.objects.create(
                    user=u,
                    tenant=nust_tenant,
                    notification_type=Notification.NotificationType.RESULT_PUBLISHED,
                    title=f"Results Published: {exam_published.title}",
                    message=f"Official scorecard for {exam_published.title} ({exam_published.code}) has been published. Total Score: {total_awarded:.1f} / {exam_published.total_marks} pts.",
                    link_url=f"/submissions/exams/{exam_published.id}/result/",
                    created_at=now - timedelta(days=4)
                )

            # ── POPULATE ATTEMPTS & ALLOCATIONS FOR EXAM 2 (Grading Queue) ─────
            GraderAllocation.objects.create(
                tenant=nust_tenant, exam=exam_grading, grader=users_map['grader.zainab'],
                candidate_range_start=1, candidate_range_end=5, sla_deadline=now + timedelta(hours=12),
                status=GraderAllocation.Status.IN_PROGRESS
            )
            GraderAllocation.objects.create(
                tenant=nust_tenant, exam=exam_grading, grader=users_map['grader.tariq'],
                candidate_range_start=6, candidate_range_end=10, sla_deadline=now + timedelta(hours=18),
                status=GraderAllocation.Status.PENDING
            )

            exam2_questions = [
                a.question for a in ExamQuestionAssignment.objects.filter(section__exam=exam_grading).select_related('question').order_by('section__order', 'order')
            ]
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
                for q_idx, q in enumerate(exam2_questions, 1):
                    AttemptAnswer.objects.create(
                        attempt=att,
                        question=q,
                        order_in_attempt=q_idx,
                        text_response=f"Student response for {q.prompt[:30]}..." if q.is_subjective else "",
                        is_graded=False
                    )
                GradeModeration.objects.create(
                    attempt=att,
                    moderator=users_map['dr.sarah.khan'],
                    status=GradeModeration.Status.PENDING
                )

            # ── POPULATE ACTIVE IN-PROGRESS SESSIONS FOR EXAM 3 (Live Ops) ─────
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

            # ── EXAM 4 (READY TO ATTEMPT TODAY): ZERO ATTEMPTS CREATED INTENTIONALLY! ──
            self.stdout.write(self.style.SUCCESS(f"  [OK] Verified: Exam 4 (LIVE-2026-CS101) has {exam_ready_to_attempt.sections.count()} sections, {exam_ready_to_attempt.total_assigned_questions} questions, and ZERO attempts for candidate testing."))

            # ------------------------------------------------------------------
            # 6. AUDIT LOGS & NOTIFICATIONS
            # ------------------------------------------------------------------
            self.stdout.write(self.style.HTTP_INFO("\n[6/7] Logging Platform Audit Trail & System Events..."))
            AuditLog.objects.create(
                tenant=nust_tenant,
                user=users_map['dr.sarah.khan'],
                category=AuditLog.ActionCategory.EXAM_OP,
                action=f"Published official results for Exam {exam_published.code}",
                ip_address="192.168.1.10",
                payload={'exam_id': exam_published.id, 'enrolled': 10, 'attempted': 9, 'sections': 4}
            )
            AuditLog.objects.create(
                tenant=nust_tenant,
                user=users_map['dr.sarah.khan'],
                category=AuditLog.ActionCategory.EXAM_OP,
                action=f"Scheduled multi-section live exam {exam_ready_to_attempt.code} with 4 sections",
                ip_address="192.168.1.10",
                payload={'exam_id': exam_ready_to_attempt.id, 'sections': 4, 'questions': exam_ready_to_attempt.total_assigned_questions}
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
      [A] ATTEMPT NEW MULTI-SECTION LIVE EXAM (Active Today):
          Click "Enter Lobby" on CS101 Live Exam -> http://127.0.0.1:8000/submissions/exams/{exam_ready_to_attempt.id}/lobby/
          Features 4 Sections (Single MCQ, Multi/Diagram, Short Answers, Long Essay), 50:50 lifelines, auto-save & auto-submit!

      [B] VIEW OFFICIAL PUBLISHED SCORECARD & PRINT TRANSCRIPT:
          Scorecard Link: http://127.0.0.1:8000/submissions/exams/{exam_published.id}/result/
          Inspect Section-by-Section scores, Examiner Rubric Feedback, and 1-Click Print PDF Transcript!

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
        self.stdout.write(f"  * Questions Authored:     {Question.objects.count()} across 5 formats")
        self.stdout.write(f"  * Exam Blueprints:        {Exam.objects.count()} blueprints with {ExamSection.objects.count()} sections")
        self.stdout.write(f"  * Question Assignments:   {ExamQuestionAssignment.objects.count()} assigned across sections")
        self.stdout.write(f"  * Roster Enrollments:     {ExamParticipantRoster.objects.count()}")
        self.stdout.write(f"  * Completed Attempts:     {ExamAttempt.objects.filter(status=ExamAttempt.Status.SUBMITTED).count()}")
        self.stdout.write(f"  * Live In-Progress:       {ExamAttempt.objects.filter(status=ExamAttempt.Status.IN_PROGRESS).count()}")
        self.stdout.write(f"  * Unattempted Live Exam:  CS101 ({exam_ready_to_attempt.sections.count()} sections, {exam_ready_to_attempt.total_assigned_questions} questions) - Ready for candidate test")
        self.stdout.write(self.style.HTTP_INFO("=" * 80) + "\n")
