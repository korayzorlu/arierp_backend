"""
Kullanım:
    python manage.py run_krs_pipeline 2
    python manage.py run_krs_pipeline 2 --rapor-tarihi 2026-06-01
"""

from datetime import date

from django.core.management.base import BaseCommand, CommandError

from krs.services.pipeline import run_krs_pipeline


class Command(BaseCommand):
    help = "KRS (temerrüt/kapama) pipeline'ını elle çalıştırır."

    def add_arguments(self, parser):
        parser.add_argument("company_id", type=int)
        parser.add_argument(
            "--rapor-tarihi", type=str, default=None,
            help="YYYY-MM-DD formatında rapor tarihi, verilmezse bugün kullanılır.",
        )

    def handle(self, *args, **options):
        rapor_tarihi = None
        if options["rapor_tarihi"]:
            try:
                rapor_tarihi = date.fromisoformat(options["rapor_tarihi"])
            except ValueError as exc:
                raise CommandError(f"Geçersiz tarih formatı: {exc}")

        count = run_krs_pipeline(options["company_id"], rapor_tarihi)
        self.stdout.write(self.style.SUCCESS(f"{count} sözleşme için KRS hesaplandı."))
