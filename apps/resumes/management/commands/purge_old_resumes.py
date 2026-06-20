"""Delete anonymous drafts untouched for a while (data hygiene for no-login app)."""
from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.resumes.models import Resume


class Command(BaseCommand):
    help = "Delete resumes not updated in the last N days (default 90)."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=90)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=options["days"])
        qs = Resume.objects.filter(updated_at__lt=cutoff)
        count = qs.count()
        if options["dry_run"]:
            self.stdout.write(f"[dry-run] would delete {count} resume(s).")
            return
        qs.delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} old resume(s)."))
