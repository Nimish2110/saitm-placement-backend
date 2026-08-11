import uuid
from django.db import models
from django.conf import settings


class StudentProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile")

    # ---- Mandatory (registration step 1) ----
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    college_email = models.EmailField()
    personal_email = models.EmailField(blank=True)
    home_address = models.TextField()
    current_residence = models.TextField()
    course = models.CharField(max_length=100)
    batch = models.CharField(max_length=10)
    roll_no = models.CharField(max_length=50, unique=True)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    backlogs = models.PositiveIntegerField(default=0)

    # ---- Optional (registration step 2, skippable) ----
    tenth_percentage = models.CharField(max_length=10, blank=True)
    twelfth_percentage = models.CharField(max_length=10, blank=True)
    achievements = models.TextField(blank=True)
    certifications = models.TextField(blank=True)
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    # ---- NEW: bulk-import / invite-link registration ----
    invite_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invite_sent_at = models.DateTimeField(null=True, blank=True)
    registration_completed = models.BooleanField(default=False)

    # ---- Application-form fields that DO carry over/prefill between applications ----
    class Gender(models.TextChoices):
        MALE = "Male", "Male"
        FEMALE = "Female", "Female"
        UNSPECIFIED = "Prefer not to say", "Prefer not to say"

    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    tenth_board = models.CharField(max_length=100, blank=True)
    tenth_year_of_passing = models.CharField(max_length=4, blank=True)
    twelfth_board = models.CharField(max_length=100, blank=True)
    twelfth_year_of_passing = models.CharField(max_length=4, blank=True)

    graduation_course = models.CharField(max_length=150, blank=True)
    graduation_percentage = models.CharField(max_length=10, blank=True)
    current_semester_percentage = models.CharField(max_length=10, blank=True)

    has_education_gap = models.BooleanField(null=True, blank=True)
    current_location = models.CharField(max_length=150, blank=True)
    hometown_location = models.CharField(max_length=150, blank=True)

    has_internship_experience = models.BooleanField(null=True, blank=True)
    internship_months = models.PositiveIntegerField(null=True, blank=True)

    # ---- Verification / status ----
    email_verified = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_expires_at = models.DateTimeField(null=True, blank=True)
    announcements_last_seen_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.roll_no})"


class StudentDocument(models.Model):
    """
    A student's reusable document library — up to 5 saved files per type.
    Used both from the Profile page directly, and from the application form's
    "Choose from Profile" option so students don't have to re-upload the same
    resume/Aadhar/marksheet every time they apply somewhere.
    """
    class DocType(models.TextChoices):
        RESUME = "resume", "Resume"
        AADHAR = "aadhar", "Aadhar Card"
        TENTH_MARKSHEET = "tenth_marksheet", "10th Marksheet"
        TWELFTH_MARKSHEET = "twelfth_marksheet", "12th Marksheet"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="documents")
    doc_type = models.CharField(max_length=20, choices=DocType.choices)
    file = models.FileField(upload_to="student_documents/%Y/%m/")
    original_filename = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.student.full_name} — {self.doc_type} — {self.original_filename}"


class Remark(models.Model):
    """
    A note a Placement Manager leaves on a student's profile — e.g. flagging
    an incomplete profile. Shows up in the student's own notifications.
    """
    is_read = models.BooleanField(default=False)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="remarks")
    placement_manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="remarks_given")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Remark for {self.student.full_name} — {self.message[:40]}"

class ResumeDraft(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="resume_drafts")
    title = models.CharField(max_length=150, default="Untitled Resume")
    template = models.CharField(max_length=30, default="classic")
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.student.full_name} — {self.title}"