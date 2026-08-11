from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    full_name = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "password", "full_name"]

    def create(self, validated_data):
        full_name = validated_data.pop("full_name")
        email = validated_data["email"]
        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data["password"],
            first_name=full_name,
            role=User.Role.STUDENT,
            is_active=False,  # activated only after OTP verification
        )
        return user


class PMRegisterSerializer(serializers.ModelSerializer):
    """
    PM self-registration — creates the account INACTIVE. An admin must
    approve it (see ApprovePMView) before the PM can actually log in.
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    full_name = serializers.CharField(write_only=True)
    phone = serializers.CharField(max_length=20)
    employee_id = serializers.CharField(max_length=50, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["email", "password", "full_name", "phone", "employee_id"]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def create(self, validated_data):
        full_name = validated_data.pop("full_name")
        email = validated_data["email"]
        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data["password"],
            first_name=full_name,
            phone=validated_data.get("phone", ""),
            employee_id=validated_data.get("employee_id", ""),
            role=User.Role.PLACEMENT_MANAGER,
            is_active=False,
        )
        return user


class PendingPMSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="first_name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "full_name", "email", "phone", "employee_id", "created_at"]


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
