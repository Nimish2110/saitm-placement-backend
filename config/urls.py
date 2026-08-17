from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/students/", include("students.urls")),
    path("api/assessments/", include("assessments.urls")),
    path("api/announcements/", include("announcements.urls")),
    path("api/", include("placements.urls")),
]