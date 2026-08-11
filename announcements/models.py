import uuid
from django.db import models
from django.conf import settings


class Announcement(models.Model):
    class TargetType(models.TextChoices):
        ALL = "all", "All Students"
        FILTERED = "filtered", "Specific Courses/Batches"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    message = models.TextField()
    target_type = models.CharField(max_length=10, choices=TargetType.choices, default=TargetType.ALL)
    eligible_courses = models.JSONField(default=list, blank=True)  # empty when target_type=ALL
    eligible_batches = models.JSONField(default=list, blank=True)  # empty when target_type=ALL
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="announcements_posted")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def is_visible_to(self, profile):
        """profile is a StudentProfile."""
        if self.target_type == self.TargetType.ALL:
            return True
        return profile.course in self.eligible_courses and profile.batch in self.eligible_batches