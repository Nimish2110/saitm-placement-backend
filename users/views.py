import random
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from students.models import StudentProfile
from .permissions import IsAdmin
from .serializers import RegisterSerializer, PMRegisterSerializer, VerifyOTPSerializer, PendingPMSerializer

User = get_user_model()


def _tokens_for(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        otp = f"{random.randint(0, 999999):06d}"
        StudentProfile.objects.create(
            user=user,
            full_name=user.first_name,
            college_email=user.email,
            otp_code=otp,
            otp_expires_at=timezone.now() + timedelta(minutes=10),
            phone="", home_address="", current_residence="", course="", batch="", roll_no=f"pending-{user.id}",
        )

        send_mail(
            subject="SAITM Placement Portal — Your verification OTP",
            message=(
                f"Hi {user.first_name},\n\n"
                f"Your OTP to verify your SAITM Placement Portal account is: {otp}\n"
                f"This code expires in 10 minutes.\n\n"
                f"If you didn't request this, ignore this email.\n\n"
                f"— SAITM T&P Cell"
            ),
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response({"detail": "Registered. OTP sent to your email."}, status=status.HTTP_201_CREATED)


class PMRegisterView(APIView):
    """
    PM self-registration. The account is created INACTIVE — no tokens are
    returned, because there's nothing to log into yet. An admin has to
    approve the application first (see ApprovePMView).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PMRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Registration submitted. An admin will review your application — you'll get an email once it's approved."},
            status=status.HTTP_201_CREATED,
        )


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        try:
            user = User.objects.get(email=email)
            profile = user.student_profile
        except (User.DoesNotExist, StudentProfile.DoesNotExist):
            return Response({"detail": "Invalid email."}, status=status.HTTP_400_BAD_REQUEST)

        if profile.otp_code != otp or profile.otp_expires_at < timezone.now():
            return Response({"detail": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

        profile.email_verified = True
        profile.otp_code = None
        profile.save()
        user.is_active = True
        user.save()

        return Response({"detail": "Verified.", **_tokens_for(user)})


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = User.objects.filter(email=email).first()

        if not user or not user.check_password(password):
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_active:
            if user.role == "placement_manager":
                message = "Your registration is still awaiting admin approval. You'll get an email once it's approved."
            else:
                message = "Account not verified yet."
            return Response({"detail": message}, status=status.HTTP_403_FORBIDDEN)

        return Response({"role": user.role, **_tokens_for(user)})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "id": str(request.user.id),
            "email": request.user.email,
            "role": request.user.role,
            "full_name": request.user.first_name,
            "phone": request.user.phone,
            "employee_id": request.user.employee_id,
            "profile_photo": request.build_absolute_uri(request.user.profile_photo.url) if request.user.profile_photo else None,
        })

    def patch(self, request):
        """Lets a PM (or anyone) update their own phone / employee ID."""
        if "phone" in request.data:
            request.user.phone = request.data["phone"]
        if "employee_id" in request.data:
            request.user.employee_id = request.data["employee_id"]
        request.user.save()
        return self.get(request)


class MyPhotoView(APIView):
    """
    PATCH /api/auth/me/photo/ — upload/replace your profile photo.
    Works for both students and PMs, since profile_photo lives on User.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request):
        photo = request.FILES.get("photo")
        if not photo:
            return Response({"detail": "No photo provided."}, status=status.HTTP_400_BAD_REQUEST)

        allowed_types = ["image/jpeg", "image/jpg", "image/png"]
        if photo.content_type not in allowed_types:
            return Response({"detail": "Photo must be a JPG or PNG."}, status=status.HTTP_400_BAD_REQUEST)
        if photo.size > 5 * 1024 * 1024:
            return Response({"detail": "Photo must be under 5 MB."}, status=status.HTTP_400_BAD_REQUEST)

        request.user.profile_photo = photo
        request.user.save()
        return Response({
            "profile_photo": request.build_absolute_uri(request.user.profile_photo.url),
        })

    def delete(self, request):
        request.user.profile_photo.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PMCountView(APIView):
    """GET /api/auth/admin/pm-count/ — how many PMs are currently active (approved & working)."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        count = User.objects.filter(role=User.Role.PLACEMENT_MANAGER, is_active=True).count()
        return Response({"count": count})


class PendingPMListView(generics.ListAPIView):
    """GET /api/auth/admin/pm-pending/ — PM applications awaiting approval."""
    serializer_class = PendingPMSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return User.objects.filter(role=User.Role.PLACEMENT_MANAGER, is_active=False).order_by("-created_at")

class ActivePMListView(generics.ListAPIView):
    """GET /api/auth/admin/pm-active/ — currently approved & working PMs (same fields as the pending list)."""
    serializer_class = PendingPMSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return User.objects.filter(role=User.Role.PLACEMENT_MANAGER, is_active=True).order_by("-created_at")

class ApprovePMView(APIView):
    """POST /api/auth/admin/pm-pending/<id>/accept/ — approve a pending PM, email them the good news."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk, role=User.Role.PLACEMENT_MANAGER, is_active=False)
        except User.DoesNotExist:
            return Response({"detail": "Pending application not found."}, status=status.HTTP_404_NOT_FOUND)

        user.is_active = True
        user.save()

        login_url = f"{settings.FRONTEND_URL}/pm-login"
        send_mail(
            subject="SAITM Placement Portal — Your Placement Manager registration is approved",
            message=(
                f"Hi {user.first_name},\n\n"
                f"Your registration as a Placement Manager on the SAITM Placement Portal has been approved by the admin.\n\n"
                f"You can now log in here: {login_url}\n\n"
                f"— SAITM Placement Portal"
            ),
            from_email=None,
            recipient_list=[user.email],
            fail_silently=True,
        )
        return Response({"detail": "Approved."})


class RejectPMView(APIView):
    """POST /api/auth/admin/pm-pending/<id>/reject/ — decline a pending PM application (deletes it, they can reapply)."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk, role=User.Role.PLACEMENT_MANAGER, is_active=False)
        except User.DoesNotExist:
            return Response({"detail": "Pending application not found."}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)