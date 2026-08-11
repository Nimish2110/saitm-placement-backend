from django.urls import path
from . import views

urlpatterns = [
    path("", views.AssessmentListView.as_view(), name="assessment-list"),
    path("my-attempts/", views.MyAttemptsView.as_view(), name="my-attempts"),
    path("leaderboard/", views.LeaderboardView.as_view(), name="leaderboard"),
    path("attempts/<uuid:attempt_id>/", views.AttemptStateView.as_view(), name="attempt-state"),
    path("attempts/<uuid:attempt_id>/answer/", views.SaveAnswerView.as_view(), name="attempt-answer"),
    path("attempts/<uuid:attempt_id>/submit/", views.SubmitAttemptView.as_view(), name="attempt-submit"),
    path("<uuid:pk>/", views.AssessmentDetailView.as_view(), name="assessment-detail"),
    path("<uuid:pk>/start/", views.StartAttemptView.as_view(), name="assessment-start"),
]