from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsAdmin
from students.models import StudentProfile
from placements.models import Application, Drive, ResumeSampleTemplate
from assessments.models import AssessmentAttempt
from announcements.models import Announcement

from django.contrib.auth import get_user_model
User = get_user_model()


class DeleteStudentView(APIView):
    """
    DELETE /api/students/admin/<uuid:profile_id>/delete/
    Keyed by StudentProfile id — that's what the Admin Student Database
    table already has, no need to separately expose the User id.
    Removes the student and every trace of them, in an explicit safe order.
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def delete(self, request, profile_id):
        try:
            profile = StudentProfile.objects.select_related("user").get(id=profile_id)
        except StudentProfile.DoesNotExist:
            return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        user = profile.user

        with transaction.atomic():
            AssessmentAttempt.objects.filter(student=user).delete()
            Application.objects.filter(student=user).delete()

            for doc in profile.documents.all():
                if doc.file:
                    doc.file.delete(save=False)
            profile.documents.all().delete()
            profile.remarks.all().delete()
            profile.resume_drafts.all().delete()

            if user.profile_photo:
                user.profile_photo.delete(save=False)

            profile.delete()
            user.delete()

        return Response({"detail": "Student and all related data deleted."}, status=status.HTTP_200_OK)


class DeletePlacementManagerView(APIView):
    """DELETE /api/students/admin/pm/<uuid:user_id>/delete/ — PMs have no separate profile model, keyed by User id directly."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def delete(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, role="placement_manager")
        except User.DoesNotExist:
            return Response({"detail": "Placement Manager not found."}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            Drive.objects.filter(posted_by=user).update(posted_by=None)
            ResumeSampleTemplate.objects.filter(uploaded_by=user).update(uploaded_by=None)
            Announcement.objects.filter(created_by=user).update(created_by=None)

            if user.profile_photo:
                user.profile_photo.delete(save=False)

            user.delete()

        return Response({"detail": "Placement Manager account deleted. Drives/formats/announcements they created were kept, now unattributed."}, status=status.HTTP_200_OK)