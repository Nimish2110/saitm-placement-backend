from django.core.management.base import BaseCommand
from assessments.models import Assessment, AssessmentQuestion


WEB_DEV_QUESTIONS = [
    ("Which HTTP method is idempotent and typically used to retrieve data without side effects?",
     "POST", "GET", "DELETE", "PATCH", "B"),
    ("In React, which hook is used to perform side effects like data fetching?",
     "useState", "useReducer", "useEffect", "useMemo", "C"),
    ("What does CSS stand for?",
     "Computer Style Sheets", "Cascading Style Sheets", "Creative Style System", "Colorful Style Sheets", "B"),
    ("Which of these is NOT a valid HTTP status code category?",
     "2xx Success", "3xx Redirection", "4xx Client Error", "6xx Server Timeout", "D"),
    ("In JavaScript, which keyword declares a block-scoped variable that cannot be reassigned?",
     "var", "let", "const", "static", "C"),
    ("What is the primary purpose of an index in a relational database?",
     "To store backup copies of data", "To speed up data retrieval", "To enforce foreign keys", "To encrypt data", "B"),
    ("Which of these is a NoSQL database?",
     "PostgreSQL", "MySQL", "MongoDB", "Oracle", "C"),
    ("In REST APIs, which status code indicates a resource was successfully created?",
     "200", "201", "204", "400", "B"),
    ("What does \"CI/CD\" stand for in software engineering?",
     "Code Integration / Code Deployment", "Continuous Integration / Continuous Deployment",
     "Central Index / Central Directory", "Client Interface / Client Design", "B"),
    ("Which data structure follows LIFO (Last In, First Out) ordering?",
     "Queue", "Stack", "Linked List", "Array", "B"),
]

APTITUDE_QUESTIONS = [
    ("If a train travels 60 km in 45 minutes, what is its speed in km/h?",
     "60 km/h", "80 km/h", "90 km/h", "75 km/h", "B"),
    ("Find the next number in the series: 2, 6, 12, 20, 30, ?",
     "40", "42", "36", "38", "B"),
    ("If 5 workers can complete a task in 12 days, how many days will 10 workers take (same work rate)?",
     "6", "24", "10", "8", "A"),
    ("What is 15% of 240?",
     "30", "36", "32", "40", "B"),
    ("A is twice as old as B. If the sum of their ages is 30, what is B's age?",
     "10", "15", "20", "12", "A"),
    ("Which word is the odd one out?",
     "Apple", "Banana", "Carrot", "Mango", "C"),
    ("If CAT is coded as DBU, how is DOG coded (same letter-shift pattern)?",
     "EPH", "EPI", "FQH", "EQH", "A"),
    ("A sum of money doubles itself in 8 years at simple interest. What is the rate of interest per annum?",
     "10%", "12.5%", "15%", "8%", "B"),
    ("Complete the analogy: Pen is to Write as Knife is to ___",
     "Sharp", "Cut", "Kitchen", "Metal", "B"),
    ("If today is Wednesday, what day will it be after 17 days?",
     "Monday", "Tuesday", "Saturday", "Sunday", "C"),
]


class Command(BaseCommand):
    help = "Seeds 2 real practice assessments with 10 verified MCQs each."

    def handle(self, *args, **options):
        self._seed(
            title="Full Stack Developer Assessment",
            description="Comprehensive assessment for full stack development skills covering React, Node.js, databases, and general web development practices.",
            category="Computer Science & IT",
            difficulty=Assessment.Difficulty.MEDIUM,
            duration_minutes=15,
            pass_percentage=60,
            tags=["Coding", "Programming", "Web Development"],
            questions=WEB_DEV_QUESTIONS,
        )
        self._seed(
            title="Quantitative Aptitude & Logical Reasoning",
            description="General aptitude and reasoning assessment covering arithmetic, series completion, coding-decoding, and analogies — relevant across every branch.",
            category="Aptitude",
            difficulty=Assessment.Difficulty.EASY,
            duration_minutes=20,
            pass_percentage=60,
            tags=["Aptitude", "Reasoning", "Campus Placement"],
            questions=APTITUDE_QUESTIONS,
        )
        self.stdout.write(self.style.SUCCESS("Seeded 2 assessments with 10 questions each."))

    def _seed(self, title, description, category, difficulty, duration_minutes, pass_percentage, tags, questions):
        assessment, created = Assessment.objects.get_or_create(
            title=title,
            defaults=dict(
                description=description, category=category, difficulty=difficulty,
                duration_minutes=duration_minutes, pass_percentage=pass_percentage, tags=tags,
            ),
        )
        if not created:
            self.stdout.write(f"'{title}' already exists — skipping (delete it first to reseed).")
            return

        for i, (text, a, b, c, d, correct) in enumerate(questions, start=1):
            AssessmentQuestion.objects.create(
                assessment=assessment, order=i, question_text=text,
                option_a=a, option_b=b, option_c=c, option_d=d,
                correct_option=correct, points=10,
            )
        self.stdout.write(f"Created '{title}' with {len(questions)} questions.")