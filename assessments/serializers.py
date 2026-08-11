from rest_framework import serializers
from .models import Assessment, AssessmentQuestion, AssessmentAttempt


class AssessmentListSerializer(serializers.ModelSerializer):
    """Card view — matches the Browse Assessments grid."""
    question_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Assessment
        fields = ["id", "title", "description", "category", "difficulty", "duration_minutes", "pass_percentage", "tags", "question_count"]


class AssessmentDetailSerializer(serializers.ModelSerializer):
    """Overview page — before starting."""
    question_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Assessment
        fields = ["id", "title", "description", "category", "difficulty", "duration_minutes", "pass_percentage", "tags", "question_count"]


class QuestionForAttemptSerializer(serializers.ModelSerializer):
    """
    Used ONLY while an attempt is in progress. Deliberately excludes
    correct_option — the student must never receive the answer key before
    submitting, no matter how the frontend calls this endpoint.
    """
    class Meta:
        model = AssessmentQuestion
        fields = ["id", "order", "question_text", "option_a", "option_b", "option_c", "option_d", "points"]


class AttemptStartSerializer(serializers.Serializer):
    attempt_id = serializers.UUIDField()
    assessment_title = serializers.CharField()
    duration_minutes = serializers.IntegerField()
    questions = QuestionForAttemptSerializer(many=True)


class QuestionResultSerializer(serializers.ModelSerializer):
    """Only ever returned AFTER submission — safe to include the correct answer here."""
    your_answer = serializers.SerializerMethodField()
    is_correct = serializers.SerializerMethodField()

    class Meta:
        model = AssessmentQuestion
        fields = ["id", "order", "question_text", "option_a", "option_b", "option_c", "option_d", "correct_option", "points", "your_answer", "is_correct"]

    def get_your_answer(self, obj):
        answers = self.context.get("answers", {})
        return answers.get(str(obj.id))

    def get_is_correct(self, obj):
        answers = self.context.get("answers", {})
        return answers.get(str(obj.id)) == obj.correct_option


class AttemptResultSerializer(serializers.ModelSerializer):
    assessment_title = serializers.CharField(source="assessment.title", read_only=True)
    pass_percentage = serializers.IntegerField(source="assessment.pass_percentage", read_only=True)
    questions = serializers.SerializerMethodField()

    class Meta:
        model = AssessmentAttempt
        fields = ["id", "assessment_title", "score", "total_possible", "passed", "pass_percentage", "submitted_at", "questions"]

    def get_questions(self, obj):
        questions = obj.assessment.questions.all()
        return QuestionResultSerializer(questions, many=True, context={"answers": obj.answers}).data


class MyAttemptSerializer(serializers.ModelSerializer):
    assessment_title = serializers.CharField(source="assessment.title", read_only=True)

    class Meta:
        model = AssessmentAttempt
        fields = ["id", "assessment", "assessment_title", "score", "total_possible", "passed", "started_at", "submitted_at"]


class LeaderboardEntrySerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    student_name = serializers.CharField()
    roll_no = serializers.CharField()
    course = serializers.CharField()
    total_score = serializers.IntegerField()
    assessments_taken = serializers.IntegerField()