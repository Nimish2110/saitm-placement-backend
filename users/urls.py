from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("pm-register/", views.PMRegisterView.as_view(), name="pm-register"),
    path("verify-otp/", views.VerifyOTPView.as_view(), name="verify-otp"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("me/", views.MeView.as_view(), name="me"),
    path("me/photo/", views.MyPhotoView.as_view(), name="my-photo"),
    path("admin/pm-count/", views.PMCountView.as_view(), name="admin-pm-count"),
    path("admin/pm-pending/", views.PendingPMListView.as_view(), name="admin-pm-pending"),
    path("admin/pm-pending/<uuid:pk>/accept/", views.ApprovePMView.as_view(), name="admin-pm-accept"),
    path("admin/pm-pending/<uuid:pk>/reject/", views.RejectPMView.as_view(), name="admin-pm-reject"),
    path("admin/pm-active/", views.ActivePMListView.as_view(), name="admin-pm-active"),
]