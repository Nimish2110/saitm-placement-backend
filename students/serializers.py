from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from .models import StudentProfile, StudentDocument, Remark, ResumeDraft


class StudentMandatorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = [
            "full_name", "phone", "college_email", "personal_email",
            "home_address", "current_residence", "course", "batch",
            "roll_no", "cgpa", "backlogs",
        ]


class StudentOptionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = [
            "tenth_percentage", "twelfth_percentage",
            "achievements", "certifications", "linkedin", "github",
        ]


class StudentProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    profile_photo = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = "__all__"

    def get_profile_photo(self, obj):
        if not obj.user.profile_photo:
            return None
        request = self.context.get("request")
        url = obj.user.profile_photo.url
        return request.build_absolute_uri(url) if request else url


class StudentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ["id", "full_name", "roll_no", "college_email", "phone", "course", "batch", "cgpa"]


class StudentApplicationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = [
            "full_name", "gender", "roll_no", "date_of_birth", "course",
            "phone", "college_email", "batch",
            "tenth_percentage", "tenth_board", "tenth_year_of_passing",
            "twelfth_percentage", "twelfth_board", "twelfth_year_of_passing",
            "graduation_course", "graduation_percentage",
            "current_semester_percentage", "backlogs", "has_education_gap",
            "current_location", "hometown_location",
            "has_internship_experience", "internship_months",
        ]


class StudentDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentDocument
        fields = ["id", "doc_type", "file", "original_filename", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at"]

    def validate_file(self, value):
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("File must be under 10 MB.")
        allowed_types = ["application/pdf", "image/jpeg", "image/jpg", "image/png"]
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("File must be a PDF or image (JPG/PNG).")
        return value


class RemarkSerializer(serializers.ModelSerializer):
    placement_manager_name = serializers.CharField(source="placement_manager.first_name", read_only=True)

    class Meta:
        model = Remark
        fields = ["id", "student", "message", "is_read", "created_at", "placement_manager_name"]
        read_only_fields = ["id", "student", "created_at", "placement_manager_name"]


class StudentFullProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    profile_photo = serializers.SerializerMethodField()
    documents_summary = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = "__all__"

    def get_profile_photo(self, obj):
        if not obj.user.profile_photo:
            return None
        request = self.context.get("request")
        url = obj.user.profile_photo.url
        return request.build_absolute_uri(url) if request else url

    def get_documents_summary(self, obj):
        summary = {}
        for doc_type in ["resume", "aadhar", "tenth_marksheet", "twelfth_marksheet"]:
            count = obj.documents.filter(doc_type=doc_type).count()
            summary[doc_type] = {"count": count, "uploaded": count > 0}
        return summary


class ResumeDraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeDraft
        fields = ["id", "title", "template", "data", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ResumeDraftListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeDraft
        fields = ["id", "title", "template", "updated_at"]


class AdminStudentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = [
            "id", "full_name", "roll_no", "college_email", "phone",
            "course", "batch", "registration_completed", "invite_sent_at", "created_at",
        ]


class StudentInviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ["full_name", "roll_no", "college_email", "phone"]


class CompleteRegistrationSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    personal_email = serializers.EmailField(required=False, allow_blank=True)
    home_address = serializers.CharField(required=True)
    current_residence = serializers.CharField(required=True)
    course = serializers.CharField(max_length=100, required=True)
    batch = serializers.CharField(max_length=10, required=True)
    cgpa = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    backlogs = serializers.IntegerField(required=False, default=0)
    tenth_percentage = serializers.CharField(max_length=10, required=True)
    twelfth_percentage = serializers.CharField(max_length=10, required=True)
    achievements = serializers.CharField(required=False, allow_blank=True)
    certifications = serializers.CharField(required=False, allow_blank=True)
    linkedin = serializers.URLField(required=False, allow_blank=True)
    github = serializers.URLField(required=False, allow_blank=True)