import datetime
from django.db.models import Count
from django.db.models.functions import TruncWeek
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsAdmin
from django.contrib.auth import get_user_model
from students.models import StudentProfile
from .models import Drive, Application

User = get_user_model()


class AdminDashboardView(APIView):
    """
    GET /api/admin/dashboard/?from=YYYY-MM-DD&to=YYYY-MM-DD&course=&batch=

    Filter rules (deliberate, not arbitrary):
    - from/to apply to anything measured by WHEN it happened (drives posted,
      applications submitted) — never to current-state counts like "active PMs".
    - course/batch apply to anything measured by WHICH students (registration
      counts, applications via the applying student) — never to drive-only
      breakdowns like drive type, which aren't tied to a student at all.
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        today = timezone.now().date()
        from_date = parse_date(request.query_params.get("from", "")) or (today - datetime.timedelta(days=90))
        to_date = parse_date(request.query_params.get("to", "")) or today
        course = request.query_params.get("course") or None
        batch = request.query_params.get("batch") or None

        from_dt = timezone.make_aware(datetime.datetime.combine(from_date, datetime.time.min))
        to_dt = timezone.make_aware(datetime.datetime.combine(to_date, datetime.time.max))

        drives_in_range = Drive.objects.filter(posted_on__gte=from_dt, posted_on__lte=to_dt)

        students_qs = StudentProfile.objects.all()
        if course:
            students_qs = students_qs.filter(course=course)
        if batch:
            students_qs = students_qs.filter(batch=batch)

        applications_qs = Application.objects.filter(applied_on__gte=from_dt, applied_on__lte=to_dt)
        if course:
            applications_qs = applications_qs.filter(student__student_profile__course=course)
        if batch:
            applications_qs = applications_qs.filter(student__student_profile__batch=batch)

        approval_breakdown = {
            "approved": drives_in_range.filter(approval_status=Drive.ApprovalStatus.APPROVED).count(),
            "pending": drives_in_range.filter(approval_status=Drive.ApprovalStatus.PENDING).count(),
            "rejected": drives_in_range.filter(approval_status=Drive.ApprovalStatus.REJECTED).count(),
        }

        registration_breakdown = {
            "completed": students_qs.filter(registration_completed=True).count(),
            "pending": students_qs.filter(registration_completed=False).count(),
        }

        course_qs = StudentProfile.objects.all()
        if batch:
            course_qs = course_qs.filter(batch=batch)
        students_by_course = [
            {"course": r["course"], "count": r["count"]}
            for r in course_qs.exclude(course="").values("course").annotate(count=Count("id")).order_by("-count")[:8]
        ]

        top_companies = [
            {"company_name": r["drive__company_name"], "count": r["count"]}
            for r in applications_qs.values("drive__company_name").annotate(count=Count("id")).order_by("-count")[:6]
        ]

        drive_type_breakdown = [
            {"type": r["drive_type"], "count": r["count"]}
            for r in drives_in_range.values("drive_type").annotate(count=Count("id"))
        ]

        drives_trend = [
            {"week": r["week"].strftime("%d %b"), "count": r["count"]}
            for r in drives_in_range.annotate(week=TruncWeek("posted_on")).values("week").annotate(count=Count("id")).order_by("week")
        ]

        return Response({
            "kpis": {
                "companies_posted": drives_in_range.count(),
                "students_registered": students_qs.filter(registration_completed=True).count(),
                "active_pms": User.objects.filter(role="placement_manager", is_active=True).count(),
                "applications_submitted": applications_qs.count(),
            },
            "approval_breakdown": approval_breakdown,
            "registration_breakdown": registration_breakdown,
            "students_by_course": students_by_course,
            "top_companies": top_companies,
            "drive_type_breakdown": drive_type_breakdown,
            "drives_trend": drives_trend,
            "date_range": {"from": from_date.isoformat(), "to": to_date.isoformat()},
        })