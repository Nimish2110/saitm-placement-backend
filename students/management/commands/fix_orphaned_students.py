from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from students.models import StudentProfile

User = get_user_model()


class Command(BaseCommand):
    help = "One-time fix: creates a minimal StudentProfile for any student User missing one."

    def handle(self, *args, **options):
        broken = User.objects.filter(role="student", student_profile__isnull=True)
        count = broken.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS("No orphaned student accounts found — nothing to fix."))
            return

        for user in broken:
            StudentProfile.objects.create(
                user=user,
                full_name=user.first_name or user.email.split("@")[0],
                roll_no=f"fix-{str(user.id)[:20]}",
                college_email=user.email,
            )
            self.stdout.write(f"Fixed: {user.email}")

        self.stdout.write(self.style.SUCCESS(f"Fixed {count} orphaned student account(s)."))