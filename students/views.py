from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsStudent, IsPlacementManager
from .models import StudentProfile, StudentDocument, Remark
from .serializers import (
    StudentMandatorySerializer,
    StudentOptionalSerializer,
    StudentProfileSerializer,
    StudentListSerializer,
    StudentDocumentSerializer,
    StudentFullProfileSerializer,
    RemarkSerializer,
)

MAX_DOCS_BY_TYPE = {
    "resume": 5,
    "aadhar": 1,
    "tenth_marksheet": 1,
    "twelfth_marksheet": 1,
}
DEFAULT_MAX_DOCS = 1


class MyProfileView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        profile = request.user.student_profile
        return Response(StudentProfileSerializer(profile, context={"request": request}).data)


class MandatoryDetailsView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def patch(self, request):
        profile = request.user.student_profile
        serializer = StudentMandatorySerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class OptionalDetailsView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def patch(self, request):
        profile = request.user.student_profile
        serializer = StudentOptionalSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class StudentDatabaseView(generics.ListAPIView):
    serializer_class = StudentListSerializer
    permission_classes = [IsAuthenticated, IsPlacementManager]

    def get_queryset(self):
        qs = StudentProfile.objects.all()
        course = self.request.query_params.get("course")
        batch = self.request.query_params.get("batch")
        roll_no = self.request.query_params.get("roll_no")
        if course:
            qs = qs.filter(course=course)
        if batch:
            qs = qs.filter(batch=batch)
        if roll_no:
            qs = qs.filter(roll_no__icontains=roll_no)
        return qs


class StudentDocumentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/students/me/documents/?doc_type=resume  -> list this student's saved docs
    POST /api/students/me/documents/                  -> upload a new one (max 5 per type)
    """
    serializer_class = StudentDocumentSerializer
    permission_classes = [IsAuthenticated, IsStudent]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        qs = StudentDocument.objects.filter(student=self.request.user.student_profile)
        doc_type = self.request.query_params.get("doc_type")
        if doc_type:
            qs = qs.filter(doc_type=doc_type)
        return qs

    def create(self, request, *args, **kwargs):
        doc_type = request.data.get("doc_type")
        profile = request.user.student_profile
        limit = MAX_DOCS_BY_TYPE.get(doc_type, DEFAULT_MAX_DOCS)
        existing_count = StudentDocument.objects.filter(student=profile, doc_type=doc_type).count()
        if existing_count >= limit:
            return Response(
                {"detail": f"You already have {limit} saved — remove it before adding another."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        uploaded_file = self.request.data.get("file")
        original_name = uploaded_file.name if uploaded_file else ""
        serializer.save(student=self.request.user.student_profile, original_filename=original_name)


class StudentDocumentDeleteView(APIView):
    """DELETE /api/students/me/documents/<id>/ — only your own document."""
    permission_classes = [IsAuthenticated, IsStudent]

    def delete(self, request, pk):
        try:
            doc = StudentDocument.objects.get(pk=pk, student=request.user.student_profile)
        except StudentDocument.DoesNotExist:
            return Response({"detail": "Document not found."}, status=status.HTTP_404_NOT_FOUND)
        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StudentFullProfileView(APIView):
    """GET /api/students/<id>/full/ — PM only. Everything about one student, read-only."""
    permission_classes = [IsAuthenticated, IsPlacementManager]

    def get(self, request, pk):
        try:
            profile = StudentProfile.objects.get(pk=pk)
        except StudentProfile.DoesNotExist:
            return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(StudentFullProfileSerializer(profile, context={"request": request}).data)


class StudentRemarksView(generics.ListCreateAPIView):
    serializer_class = RemarkSerializer
    permission_classes = [IsAuthenticated, IsPlacementManager]

    def get_queryset(self):
        return Remark.objects.filter(student_id=self.kwargs["pk"], is_read=False)

    def perform_create(self, serializer):
        student = StudentProfile.objects.get(pk=self.kwargs["pk"])
        serializer.save(student=student, placement_manager=self.request.user)


class MyRemarksView(generics.ListAPIView):
    serializer_class = RemarkSerializer
    permission_classes = [IsAuthenticated, IsStudent]

    def get_queryset(self):
        return Remark.objects.filter(student=self.request.user.student_profile, is_read=False)


class MarkRemarkReadView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def patch(self, request, pk):
        try:
            remark = Remark.objects.get(pk=pk, student=request.user.student_profile)
        except Remark.DoesNotExist:
            return Response({"detail": "Remark not found."}, status=status.HTTP_404_NOT_FOUND)
        remark.is_read = True
        remark.save()
        return Response(status=status.HTTP_204_NO_CONTENT)