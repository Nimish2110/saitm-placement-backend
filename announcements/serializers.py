from rest_framework import serializers
from .models import Announcement


class AnnouncementSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.first_name", read_only=True)
    created_by_role = serializers.CharField(source="created_by.role", read_only=True)

    class Meta:
        model = Announcement
        fields = [
            "id", "title", "message", "target_type", "eligible_courses", "eligible_batches",
            "created_by_name", "created_by_role", "created_at",
        ]
        read_only_fields = ["id", "created_by_name", "created_by_role", "created_at"]

    def validate(self, attrs):
        target_type = attrs.get("target_type", Announcement.TargetType.ALL)
        if target_type == Announcement.TargetType.FILTERED:
            if not attrs.get("eligible_courses") or not attrs.get("eligible_batches"):
                raise serializers.ValidationError(
                    "Select at least one course and one batch when targeting specific students."
                )
        return attrs