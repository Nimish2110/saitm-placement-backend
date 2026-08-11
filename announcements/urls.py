from django.urls import path
from . import views

urlpatterns = [
    path("", views.AnnouncementListCreateView.as_view(), name="announcement-list-create"),
    path("unread-count/", views.AnnouncementUnreadCountView.as_view(), name="announcement-unread-count"),
    path("mark-seen/", views.MarkAnnouncementsSeenView.as_view(), name="announcement-mark-seen"),
    path("<uuid:pk>/", views.AnnouncementDeleteView.as_view(), name="announcement-delete"),
]