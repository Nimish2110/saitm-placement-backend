from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from users.permissions import IsPlacementManager
from .models import Drive, DriveJDFile
from .serializers import DriveJDFileSerializer


class DriveJDFileListUploadView(APIView):
    """
    GET  /api/drives/<id>/jd-files/ — anyone authenticated (PM + student) can view/download.
    POST /api/drives/<id>/jd-files/ — PM only. Accepts MULTIPLE files in one request
         via the 'files' field (not just one at a time).
    """
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsPlacementManager()]
        return [IsAuthenticated()]

    def get(self, request, drive_id):
        try:
            drive = Drive.objects.get(pk=drive_id)
        except Drive.DoesNotExist:
            return Response({"detail": "Drive not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(DriveJDFileSerializer(drive.jd_files.all(), many=True).data)

    def post(self, request, drive_id):
        try:
            drive = Drive.objects.get(pk=drive_id)
        except Drive.DoesNotExist:
            return Response({"detail": "Drive not found."}, status=status.HTTP_404_NOT_FOUND)

        uploaded_files = request.FILES.getlist("files")
        if not uploaded_files:
            return Response({"detail": "No files provided."}, status=status.HTTP_400_BAD_REQUEST)

        created = []
        errors = []
        for f in uploaded_files:
            serializer = DriveJDFileSerializer(data={"file": f})
            if serializer.is_valid():
                obj = DriveJDFile.objects.create(drive=drive, file=f, original_filename=f.name)
                created.append(DriveJDFileSerializer(obj).data)
            else:
                errors.append({"filename": f.name, "errors": serializer.errors})

        return Response({"created": created, "errors": errors}, status=status.HTTP_201_CREATED)


class DriveJDFileDeleteView(APIView):
    """DELETE /api/drives/jd-files/<file_id>/ — PM only, restricted to the drive's own poster."""
    permission_classes = [IsAuthenticated, IsPlacementManager]

    def delete(self, request, file_id):
        try:
            jd_file = DriveJDFile.objects.get(pk=file_id)
        except DriveJDFile.DoesNotExist:
            return Response({"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND)

        if jd_file.drive.posted_by_id != request.user.id:
            return Response({"detail": "You can only remove files from drives you posted."}, status=status.HTTP_403_FORBIDDEN)

        jd_file.file.delete(save=False)
        jd_file.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)