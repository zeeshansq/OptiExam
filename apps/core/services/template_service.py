import io
import csv
from typing import Tuple, Dict, Any, List

def generate_sample_roster_template(format_type: str = 'csv') -> Tuple[bytes, str, str]:
    """
    Generates a valid candidate roster import sample template with header descriptions
    and 5 realistic student records.
    Returns: (file_bytes, content_type, filename)
    """
    headers = ['registration_number', 'first_name', 'last_name', 'email', 'department', 'batch_year']
    sample_rows = [
        ['REG-2026-001', 'Ahmad', 'Khan', 'ahmad.khan@student.edu', 'Computer Science', '2026'],
        ['REG-2026-002', 'Fatima', 'Zahra', 'fatima.zahra@student.edu', 'Computer Science', '2026'],
        ['REG-2026-003', 'Bilal', 'Tariq', 'bilal.tariq@student.edu', 'Software Engineering', '2025'],
        ['REG-2026-004', 'Ayesha', 'Malik', 'ayesha.malik@student.edu', 'Electrical Engineering', '2026'],
        ['REG-2026-005', 'Hamza', 'Ali', 'hamza.ali@student.edu', 'Computer Science', '2026']
    ]

    if format_type.lower() == 'xlsx':
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Candidate Roster"
            ws.append(headers)
            for row in sample_rows:
                ws.append(row)
            
            output = io.BytesIO()
            wb.save(output)
            return (
                output.getvalue(),
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'sample_participant_roster.xlsx'
            )
        except ImportError:
            pass  # Fallback to CSV

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(sample_rows)
    return (
        output.getvalue().encode('utf-8'),
        'text/csv',
        'sample_participant_roster.csv'
    )


def generate_sample_question_bank_template(format_type: str = 'csv') -> Tuple[bytes, str, str]:
    """
    Generates a valid question bank import sample template containing all 5 supported question types.
    Returns: (file_bytes, content_type, filename)
    """
    headers = [
        'question_type', 'prompt', 'points', 'negative_points',
        'difficulty', 'blooms_level', 'topic_tags', 'options',
        'correct_options', 'model_answer', 'hint_text', 'rubric_criteria'
    ]
    sample_rows = [
        [
            'MCQ_SINGLE',
            'What is the worst-case time complexity of Merge Sort?',
            '2.0',
            '0.5',
            'MEDIUM',
            'UNDERSTAND',
            'algorithms, sorting, complexity',
            'A) O(n) | B) O(n log n) | C) O(n^2) | D) O(log n)',
            'B',
            'Merge Sort always divides array in halves and takes linear merge time: O(n log n)',
            'Think about the tree depth and linear work per level.',
            ''
        ],
        [
            'MCQ_MULTIPLE',
            'Which of the following are valid linear data structures? (Select all that apply)',
            '3.0',
            '1.0',
            'EASY',
            'REMEMBER',
            'data structures, linear',
            'A) Array | B) Binary Tree | C) Stack | D) Graph | E) Queue',
            'A, C, E',
            'Arrays, Stacks, and Queues are linear. Trees and Graphs are non-linear.',
            'Linear structures store elements sequentially.',
            ''
        ],
        [
            'IMAGE_MCQ',
            'Identify the type of CPU pipeline hazard illustrated in the attached diagram.',
            '4.0',
            '1.0',
            'HARD',
            'ANALYZE',
            'computer architecture, pipelining, hazards',
            'A) Structural Hazard | B) Data Hazard (RAW) | C) Control Hazard | D) WAW Hazard',
            'B',
            'Instruction 2 depends on the register writeback of Instruction 1 causing Read-After-Write data dependency.',
            'Observe register R1 in instruction 1 and 2.',
            ''
        ],
        [
            'SHORT_ANSWER',
            'Define polymorphism in Object-Oriented Programming and provide one short example.',
            '5.0',
            '0.0',
            'MEDIUM',
            'APPLY',
            'oop, polymorphism, java',
            '',
            '',
            'Polymorphism is the ability of an object to take many forms (e.g. method overriding where Circle and Square implement draw() differently).',
            'Think of method overriding vs overloading.',
            ''
        ],
        [
            'LONG_ESSAY',
            'Explain Dijkstra\'s Shortest Path algorithm. Include priority queue usage, edge relaxation step, and time complexity derivation.',
            '10.0',
            '0.0',
            'HARD',
            'CREATE',
            'graphs, dijkstra, algorithms',
            '',
            '',
            'Complete derivation: initialization of distances to infinity, min-heap extract-min, edge relaxation condition d(v) > d(u) + w(u,v), and overall O((V+E) log V) complexity.',
            'Focus on the relaxation property and greedy choice property.',
            'Algorithm Overview: 3.0 | Priority Queue & Complexity: 3.0 | Edge Relaxation Mechanics: 4.0'
        ]
    ]

    if format_type.lower() == 'xlsx':
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Question Bank"
            ws.append(headers)
            for row in sample_rows:
                ws.append(row)
            
            output = io.BytesIO()
            wb.save(output)
            return (
                output.getvalue(),
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'sample_question_bank.xlsx'
            )
        except ImportError:
            pass

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(sample_rows)
    return (
        output.getvalue().encode('utf-8'),
        'text/csv',
        'sample_question_bank.csv'
    )
