from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsStudent
from .models import Assessment, AssessmentQuestion, AssessmentAttempt
from .serializers import (
    AssessmentListSerializer,
    AssessmentDetailSerializer,
    QuestionForAttemptSerializer,
    AttemptResultSerializer,
    MyAttemptSerializer,
)

VALID_OPTIONS = {"A", "B", "C", "D"}


class AssessmentListView(generics.ListAPIView):
    """GET /api/assessments/ — Browse Assessments grid. ?category=&difficulty="""
    serializer_class = AssessmentListSerializer
    permission_classes = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        qs = Assessment.objects.filter(is_active=True)
        category = self.request.query_params.get("category")
        difficulty = self.request.query_params.get("difficulty")
        if category and category != "All":
            qs = qs.filter(category=category)
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        return qs

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        data = []
        for a in qs:
            item = AssessmentListSerializer(a).data
            item["question_count"] = a.question_count
            data.append(item)
        return Response(data)


class AssessmentDetailView(APIView):
    """GET /api/assessments/<id>/ — overview page before starting."""
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request, pk):
        try:
            assessment = Assessment.objects.get(pk=pk, is_active=True)
        except Assessment.DoesNotExist:
            return Response({"detail": "Assessment not found."}, status=status.HTTP_404_NOT_FOUND)
        data = AssessmentDetailSerializer(assessment).data
        data["question_count"] = assessment.question_count
        return Response(data)


class StartAttemptView(APIView):
    """POST /api/assessments/<id>/start/ — begin a fresh attempt. Questions returned WITHOUT correct answers."""
    permission_classes = [IsAuthenticated, IsStudent]

    def post(self, request, pk):
        try:
            assessment = Assessment.objects.get(pk=pk, is_active=True)
        except Assessment.DoesNotExist:
            return Response({"detail": "Assessment not found."}, status=status.HTTP_404_NOT_FOUND)

        attempt = AssessmentAttempt.objects.create(assessment=assessment, student=request.user)
        questions = QuestionForAttemptSerializer(assessment.questions.all(), many=True).data
        return Response({
            "attempt_id": str(attempt.id),
            "assessment_title": assessment.title,
            "duration_minutes": assessment.duration_minutes,
            "questions": questions,
        }, status=status.HTTP_201_CREATED)


class AttemptStateView(APIView):
    """GET /api/assessments/attempts/<id>/ — resume an in-progress attempt, or view results if already submitted."""
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request, attempt_id):
        try:
            attempt = AssessmentAttempt.objects.get(pk=attempt_id, student=request.user)
        except AssessmentAttempt.DoesNotExist:
            return Response({"detail": "Attempt not found."}, status=status.HTTP_404_NOT_FOUND)

        if attempt.submitted_at:
            return Response(AttemptResultSerializer(attempt).data)

        questions = QuestionForAttemptSerializer(attempt.assessment.questions.all(), many=True).data
        return Response({
            "attempt_id": str(attempt.id),
            "assessment_title": attempt.assessment.title,
            "duration_minutes": attempt.assessment.duration_minutes,
            "questions": questions,
            "answers": attempt.answers,
            "submitted": False,
        })


class SaveAnswerView(APIView):
    """PATCH /api/assessments/attempts/<id>/answer/ — body: {question_id, selected_option}"""
    permission_classes = [IsAuthenticated, IsStudent]

    def patch(self, request, attempt_id):
        try:
            attempt = AssessmentAttempt.objects.get(pk=attempt_id, student=request.user)
        except AssessmentAttempt.DoesNotExist:
            return Response({"detail": "Attempt not found."}, status=status.HTTP_404_NOT_FOUND)

        if attempt.submitted_at:
            return Response({"detail": "This attempt has already been submitted."}, status=status.HTTP_400_BAD_REQUEST)

        question_id = str(request.data.get("question_id"))
        selected = request.data.get("selected_option")
        if selected not in VALID_OPTIONS:
            return Response({"detail": "selected_option must be one of A, B, C, D."}, status=status.HTTP_400_BAD_REQUEST)
        if not AssessmentQuestion.objects.filter(id=question_id, assessment=attempt.assessment).exists():
            return Response({"detail": "Question does not belong to this assessment."}, status=status.HTTP_400_BAD_REQUEST)

        attempt.answers[question_id] = selected
        attempt.save()
        return Response({"answers": attempt.answers})


class SubmitAttemptView(APIView):
    """POST /api/assessments/attempts/<id>/submit/ — score it, lock it, return full results with correct answers."""
    permission_classes = [IsAuthenticated, IsStudent]

    def post(self, request, attempt_id):
        try:
            attempt = AssessmentAttempt.objects.get(pk=attempt_id, student=request.user)
        except AssessmentAttempt.DoesNotExist:
            return Response({"detail": "Attempt not found."}, status=status.HTTP_404_NOT_FOUND)

        if attempt.submitted_at:
            return Response(AttemptResultSerializer(attempt).data)  # idempotent

        questions = attempt.assessment.questions.all()
        total_possible = sum(q.points for q in questions)
        score = sum(q.points for q in questions if attempt.answers.get(str(q.id)) == q.correct_option)

        attempt.score = score
        attempt.total_possible = total_possible
        attempt.passed = total_possible > 0 and (score / total_possible * 100) >= attempt.assessment.pass_percentage
        attempt.submitted_at = timezone.now()
        attempt.save()

        return Response(AttemptResultSerializer(attempt).data, status=status.HTTP_200_OK)


class MyAttemptsView(generics.ListAPIView):
    """GET /api/assessments/my-attempts/ — this student's own attempt history ('My Performance')."""
    serializer_class = MyAttemptSerializer
    permission_classes = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        return AssessmentAttempt.objects.filter(student=self.request.user, submitted_at__isnull=False)


class LeaderboardView(APIView):
    """
    GET /api/assessments/leaderboard/ — ranks students by total score, taking
    their BEST attempt per assessment (so retaking doesn't let you double-count).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        submitted = AssessmentAttempt.objects.filter(submitted_at__isnull=False).select_related("student__student_profile", "assessment")

        best_per_student_assessment = {}
        for a in submitted:
            key = (a.student_id, a.assessment_id)
            if key not in best_per_student_assessment or a.score > best_per_student_assessment[key].score:
                best_per_student_assessment[key] = a

        totals = {}
        for a in best_per_student_assessment.values():
            sid = a.student_id
            profile = getattr(a.student, "student_profile", None)
            if not profile:
                continue
            if sid not in totals:
                totals[sid] = {
                    "student_name": profile.full_name,
                    "roll_no": profile.roll_no,
                    "course": profile.course,
                    "total_score": 0,
                    "assessments_taken": 0,
                }
            totals[sid]["total_score"] += a.score
            totals[sid]["assessments_taken"] += 1

        ranked = sorted(totals.values(), key=lambda x: x["total_score"], reverse=True)
        limit = int(request.query_params.get("limit", 20))
        results = []
        for i, entry in enumerate(ranked[:limit], start=1):
            results.append({"rank": i, **entry})

        my_entry = None
        my_totals = totals.get(request.user.id)
        if my_totals:
            my_rank = next((i for i, e in enumerate(ranked, start=1) if e["roll_no"] == my_totals["roll_no"]), None)
            my_entry = {"rank": my_rank, **my_totals}

        return Response({"leaderboard": results, "me": my_entry})