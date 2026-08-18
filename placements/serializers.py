from rest_framework import serializers
from .models import Drive, Application, ResumeSampleTemplate, DriveJDFile


class DriveJDFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriveJDFile
        fields = ["id", "file", "original_filename", "uploaded_at"]
        read_only_fields = ["id", "original_filename", "uploaded_at"]

    def validate_file(self, value):
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("Each file must be under 10 MB.")
        allowed_types = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Only PDF or Word documents are allowed.")
        return value


class DriveSerializer(serializers.ModelSerializer):
    posted_by_name = serializers.CharField(source="posted_by.get_full_name", read_only=True, default="Placement Manager")
    is_eligible = serializers.SerializerMethodField()
    applications_count = serializers.SerializerMethodField()
    jd_files = DriveJDFileSerializer(many=True, read_only=True)

    class Meta:
        model = Drive
        fields = [
            "id", "drive_type", "company_name", "company_website", "jd_text", "jd_files",
            "profiles_offered", "job_location", "eligible_courses", "eligible_batches",
            "ctc", "process_details", "last_date_of_application",
            "company_link", "pm_note",
            "posted_by_name", "posted_on", "status", "is_eligible", "applications_count",
        ]
        read_only_fields = ["id", "posted_on", "status"]

    def get_is_eligible(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated or request.user.role != "student":
            return True  # non-student viewers (PM) — flag isn't meaningful, default True
        profile = getattr(request.user, "student_profile", None)
        if not profile:
            return False
        return profile.course in obj.eligible_courses and profile.batch in obj.eligible_batches

    def get_applications_count(self, obj):
        return obj.applications.count()
        


class ApplicationSerializer(serializers.ModelSerializer):
    """Read-only view used by the PM's Students Applied / Drives Floated pages."""
    student_name = serializers.CharField(source="student.student_profile.full_name", read_only=True)
    roll_no = serializers.CharField(source="student.student_profile.roll_no", read_only=True)
    course = serializers.CharField(source="student.student_profile.course", read_only=True)
    batch = serializers.CharField(source="student.student_profile.batch", read_only=True)
    company_name = serializers.CharField(source="drive.company_name", read_only=True)
    student_profile_id = serializers.CharField(source="student.student_profile.id", read_only=True)

    class Meta:
        model = Application
        fields = [
            "id", "student", "drive", "status", "applied_on",
            "student_name", "roll_no", "course", "batch", "company_name",
            "campus_name", "aadhar_no", "aadhar_file", "resume_file",
            "student_profile_id",
        ]
        read_only_fields = ["id", "applied_on", "student"]


class ApplicationFormSerializer(serializers.ModelSerializer):
    """
    Full application-form submission — everything the student fills in the
    in-app application modal. Handles file uploads (multipart), validates the
    mandatory Google-Form-equivalent fields server-side (never trust the
    frontend's "required" attributes alone), and is only ever saved once —
    on the actual Submit click, never on Apply Now / just opening the form.
    """

    # ---- Identity fields — editable here too, just for this application; also written back to profile ----
    full_name = serializers.CharField(max_length=150)
    roll_no = serializers.CharField(max_length=50)
    phone = serializers.CharField(max_length=20)
    college_email = serializers.EmailField()
    course = serializers.CharField(max_length=150)
    batch = serializers.CharField(max_length=10)

    # ---- Profile-persisting fields (also written back to StudentProfile) ----
    gender = serializers.ChoiceField(choices=["Male", "Female", "Prefer not to say"])
    date_of_birth = serializers.DateField()
    tenth_percentage = serializers.CharField(max_length=10)
    tenth_board = serializers.CharField(max_length=100)
    tenth_year_of_passing = serializers.CharField(max_length=4)
    twelfth_percentage = serializers.CharField(max_length=10)
    twelfth_board = serializers.CharField(max_length=100)
    twelfth_year_of_passing = serializers.CharField(max_length=4, required=False, allow_blank=True)
    graduation_course = serializers.CharField(max_length=150, required=False, allow_blank=True)
    graduation_percentage = serializers.CharField(max_length=10, required=False, allow_blank=True)
    current_semester_percentage = serializers.CharField(max_length=10)
    backlogs = serializers.IntegerField(min_value=0)
    has_education_gap = serializers.BooleanField()
    current_location = serializers.CharField(max_length=150)
    hometown_location = serializers.CharField(max_length=150)
    has_internship_experience = serializers.BooleanField()
    internship_months = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Application
        fields = [
            "campus_name", "aadhar_no", "aadhar_file", "resume_file",
            "full_name", "roll_no", "phone", "college_email", "course", "batch",
            "gender", "date_of_birth", "tenth_percentage", "tenth_board", "tenth_year_of_passing",
            "twelfth_percentage", "twelfth_board", "twelfth_year_of_passing",
            "graduation_course", "graduation_percentage", "current_semester_percentage",
            "backlogs", "has_education_gap", "current_location", "hometown_location",
            "has_internship_experience", "internship_months",
        ]

    def validate(self, attrs):
        if attrs.get("has_internship_experience") and not attrs.get("internship_months"):
            raise serializers.ValidationError({"internship_months": "Required when internship experience is Yes."})
        return attrs

    def _validate_file(self, value, field_name):
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(f"{field_name} must be under 10 MB.")
        allowed_types = ["application/pdf", "image/jpeg", "image/jpg", "image/png"]
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(f"{field_name} must be a PDF or image (JPG/PNG).")
        return value

    def validate_aadhar_file(self, value):
        return self._validate_file(value, "Aadhar card")

    def validate_resume_file(self, value):
        return self._validate_file(value, "Resume")


class ResumeSampleTemplateSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source="uploaded_by.first_name", read_only=True)

    class Meta:
        model = ResumeSampleTemplate
        fields = ["id", "name", "description", "style_tag", "file", "original_filename", "uploaded_by_name", "created_at"]
        read_only_fields = ["id", "original_filename", "uploaded_by_name", "created_at"]

    def validate_file(self, value):
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("File must be under 10 MB.")
        allowed_types = [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ]
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("File must be a PDF or Word document.")
        return value