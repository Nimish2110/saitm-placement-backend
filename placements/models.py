import uuid
from django.db import models
from django.conf import settings


class Drive(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"
    class ApprovalStatus(models.TextChoices):
        PENDING = "pending", "Pending Approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    drive_type = models.CharField(
        max_length=50,
        default="Final Placements",
        help_text="e.g. Final Placements, Internship, Internship with PPO, Pre-Placement Offer",
    )
    company_name = models.CharField(max_length=150)
    company_website = models.URLField(blank=True)
    jd_text = models.TextField(blank=True)  # pasted-in job description text, no external link needed
    profiles_offered = models.JSONField(default=list)
    job_location = models.CharField(max_length=150)
    eligible_courses = models.JSONField(default=list)
    eligible_batches = models.JSONField(default=list)
    ctc = models.CharField(max_length=100)
    process_details = models.CharField(max_length=255, blank=True)
    last_date_of_application = models.DateTimeField()
    approval_status = models.CharField(max_length=10, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="drives_approved")
    approved_on = models.DateTimeField(null=True, blank=True)

    # The ONLY link field now — students apply through our own in-app form
    # (see Application below). This is just for the (optional) companies that
    # also require students to register on their own external portal.
    company_link = models.URLField(blank=True)

    pm_note = models.TextField(blank=True)

    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="drives_posted")
    posted_on = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)

    class Meta:
        ordering = ["-posted_on"]

    def __str__(self):
        return f"{self.company_name} — {self.drive_type}"


class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = "Applied", "Applied"
        UNDER_REVIEW = "Under Review", "Under Review"
        INTERVIEW_SCHEDULED = "Interview Scheduled", "Interview Scheduled"
        SELECTED = "Selected", "Selected"
        REJECTED = "Rejected", "Rejected"
        CLOSED = "Closed", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications")
    drive = models.ForeignKey(Drive, on_delete=models.CASCADE, related_name="applications")
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.APPLIED)
    applied_on = models.DateTimeField(auto_now_add=True)

    # Per-application fields — NOT carried over from a previous application,
    # the student re-enters/re-uploads these every single time.
    campus_name = models.CharField(
        max_length=50,
        choices=[("SAITM, Gurgaon", "SAITM, Gurgaon"), ("SAITM, Delhi", "SAITM, Delhi")],
    )
    aadhar_no = models.CharField(max_length=20)
    aadhar_file = models.FileField(upload_to="applications/aadhar/%Y/%m/")
    resume_file = models.FileField(upload_to="applications/resumes/%Y/%m/")

    class Meta:
        unique_together = ("student", "drive")
        ordering = ["-applied_on"]

    def __str__(self):
        return f"{self.student} -> {self.drive}"

class DriveJDFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    drive = models.ForeignKey(Drive, on_delete=models.CASCADE, related_name="jd_files")
    file = models.FileField(upload_to="drive_jd_files/%Y/%m/")
    original_filename = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.drive.company_name} — {self.original_filename}"

class ResumeSampleTemplate(models.Model):
    """
    A real resume file (PDF/DOCX) a Placement Manager uploads as a format
    reference. Students browse and download these in Resume Builder — not
    an auto-fill template, just a real example they can view or use as a
    starting point.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    description = models.CharField(max_length=300, blank=True)
    style_tag = models.CharField(max_length=50, blank=True)  # e.g. "Modern", "Classic", "Technical"
    file = models.FileField(upload_to="resume_samples/%Y/%m/")
    original_filename = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="resume_samples_uploaded")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name