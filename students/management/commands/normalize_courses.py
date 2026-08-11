from django.core.management.base import BaseCommand
from students.models import StudentProfile

OLD_TO_NEW = {
    "B.Tech - CSE": "B.Tech - Computer Science Engineering",
    "B.Tech - CST": "B.Tech - Computer Science and Technology",
    "B.Tech - AIML": "B.Tech - Computer Science Engineering (AI-ML)",
    "B.Tech - ME": "B.Tech - Mechanical Engineering",
    "B.Tech - ETCE": "B.Tech - Electronics and Telecommunication",
    "B.Tech - CE": "B.Tech - Civil Engineering",
    "B.Tech - Civil": "B.Tech - Civil Engineering",
    "B.Tech - DS": "B.Tech - Data Science",
}


class Command(BaseCommand):
    help = "One-time fix: updates any StudentProfile.course still using the old short names to the current full names."

    def handle(self, *args, **options):
        updated = 0
        for old_name, new_name in OLD_TO_NEW.items():
            count = StudentProfile.objects.filter(course=old_name).update(course=new_name)
            if count:
                self.stdout.write(f"  {old_name!r} -> {new_name!r}: {count} student(s) updated")
                updated += count

        if updated == 0:
            self.stdout.write(self.style.SUCCESS("No outdated course names found — nothing to fix."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Done. {updated} student profile(s) updated in total."))