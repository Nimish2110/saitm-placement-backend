from django.urls import path
from . import views
from . import resume_views
from . import admin_registration_views as admin_views
from . import delete_views

urlpatterns = [
    path("me/", views.MyProfileView.as_view(), name="student-me"),
    path("me/mandatory/", views.MandatoryDetailsView.as_view(), name="student-mandatory"),
    path("me/optional/", views.OptionalDetailsView.as_view(), name="student-optional"),
    path("me/documents/", views.StudentDocumentListCreateView.as_view(), name="student-documents"),
    path("me/documents/<uuid:pk>/", views.StudentDocumentDeleteView.as_view(), name="student-document-delete"),
    path("me/remarks/", views.MyRemarksView.as_view(), name="my-remarks"),
    path("me/remarks/<uuid:pk>/read/", views.MarkRemarkReadView.as_view(), name="mark-remark-read"),
    path("resumes/", resume_views.ResumeDraftListCreateView.as_view(), name="resume-list-create"),
    path("resumes/prefill/", resume_views.ResumePrefillView.as_view(), name="resume-prefill"),
    path("resumes/<uuid:pk>/", resume_views.ResumeDraftDetailView.as_view(), name="resume-detail"),
    path("resumes/<uuid:pk>/export/pdf/", resume_views.ResumeExportPDFView.as_view(), name="resume-export-pdf"),
    path("resumes/<uuid:pk>/export/docx/", resume_views.ResumeExportDOCXView.as_view(), name="resume-export-docx"),
    path("admin/list/", admin_views.AdminStudentListView.as_view(), name="admin-student-list"),
    path("admin/bulk-import/", admin_views.BulkImportStudentsView.as_view(), name="admin-bulk-import"),
    path("admin/send-invites/", admin_views.SendInvitesView.as_view(), name="admin-send-invites"),
    path("admin/<uuid:profile_id>/delete/", delete_views.DeleteStudentView.as_view(), name="admin-delete-student"),
    path("admin/pm/<uuid:user_id>/delete/", delete_views.DeletePlacementManagerView.as_view(), name="admin-delete-pm"),
    path("invite/<uuid:token>/", admin_views.InviteDetailView.as_view(), name="invite-detail"),
    path("invite/<uuid:token>/complete/", admin_views.CompleteRegistrationView.as_view(), name="invite-complete"),
    path("<uuid:pk>/full/", views.StudentFullProfileView.as_view(), name="student-full-profile"),
    path("<uuid:pk>/remarks/", views.StudentRemarksView.as_view(), name="student-remarks"),
    path("", views.StudentDatabaseView.as_view(), name="student-database"),
]