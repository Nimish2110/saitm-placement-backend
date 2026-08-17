from django.urls import path
from . import views
from . import jd_views

urlpatterns = [
    path("drives/", views.DriveListCreateView.as_view(), name="drive-list-create"),
    path("drives/mine/", views.MyDrivesView.as_view(), name="drives-floated"),
    path("drives/<uuid:pk>/apply/", views.ApplyToDriveView.as_view(), name="drive-apply"),
    path("applications/export/", views.ExportApplicationsView.as_view(), name="applications-export"),
    path("applications/", views.ApplicationListView.as_view(), name="applications-list"),
    path("applications/mine/", views.MyApplicationsView.as_view(), name="my-applications"),
    path("resume-formats/", views.ResumeSampleTemplateListCreateView.as_view(), name="resume-format-list-create"),
    path("resume-formats/<uuid:pk>/", views.ResumeSampleTemplateDeleteView.as_view(), name="resume-format-delete"),
    path("drives/<uuid:drive_id>/jd-files/", jd_views.DriveJDFileListUploadView.as_view(), name="drive-jd-files"),
    path("drives/jd-files/<uuid:file_id>/", jd_views.DriveJDFileDeleteView.as_view(), name="drive-jd-file-delete"),
]