from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsStudent, IsPMOrAdmin
from .models import Announcement
from .serializers import AnnouncementSerializer


class AnnouncementListCreateView(generics.ListCreateAPIView):
    """
    GET  -> Student: only announcements visible to them (ALL, or filtered
            matching their own course+batch).
            PM/Admin: every announcement, for management purposes.
    POST -> PM or Admin only.
    """
    serializer_class = AnnouncementSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsPMOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = Announcement.objects.filter(is_active=True)

        if user.role == "student":
            profile = getattr(user, "student_profile", None)
            if not profile:
                return Announcement.objects.none()
            visible_ids = [a.id for a in qs if a.is_visible_to(profile)]
            return qs.filter(id__in=visible_ids)

        # PM/Admin see everything, for management
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AnnouncementDeleteView(APIView):
    """
    DELETE /api/announcements/<id>/
    PM can only delete their own announcements. Admin can delete any.
    """
    permission_classes = [IsAuthenticated, IsPMOrAdmin]

    def delete(self, request, pk):
        try:
            announcement = Announcement.objects.get(pk=pk)
        except Announcement.DoesNotExist:
            return Response({"detail": "Announcement not found."}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role == "placement_manager" and announcement.created_by_id != request.user.id:
            return Response({"detail": "You can only delete announcements you posted."}, status=status.HTTP_403_FORBIDDEN)

        announcement.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AnnouncementUnreadCountView(APIView):
    """GET /api/announcements/unread-count/ — powers the sidebar badge. Student only."""
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        profile = getattr(request.user, "student_profile", None)
        if not profile:
            return Response({"count": 0})

        visible = Announcement.objects.filter(is_active=True)
        visible = [a for a in visible if a.is_visible_to(profile)]

        if profile.announcements_last_seen_at is None:
            count = len(visible)
        else:
            count = sum(1 for a in visible if a.created_at > profile.announcements_last_seen_at)

        return Response({"count": count})


class MarkAnnouncementsSeenView(APIView):
    """POST /api/announcements/mark-seen/ — call this when the student opens the Announcements page."""
    permission_classes = [IsAuthenticated, IsStudent]

    def post(self, request):
        profile = getattr(request.user, "student_profile", None)
        if not profile:
            return Response({"detail": "No student profile."}, status=status.HTTP_400_BAD_REQUEST)
        profile.announcements_last_seen_at = timezone.now()
        profile.save()
        return Response({"detail": "Marked as seen."})