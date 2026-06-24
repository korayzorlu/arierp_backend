"""
Kullanım:
    # Günlük mod (IFS günlük KRS ile aynı: o günkü vadeli sözleşmeler)
    python manage.py run_krs_pipeline 2
    python manage.py run_krs_pipeline 2 --rapor-tarihi 2026-06-22

    # Aylık mod (ay sonu tam BDDK bildirimi için)
    python manage.py run_krs_pipeline 2 --mod aylik
    python manage.py run_krs_pipeline 2 --rapor-tarihi 2026-06-30 --mod aylik
"""

from datetime import date
from django.core.management.base import BaseCommand, CommandError
from krs.services.pipeline import run_krs_pipeline


class Command(BaseCommand):
    help = "KRS (temerrüt/kapama) pipeline'ını çalıştırır."

    def add_arguments(self, parser):
        parser.add_argument("company_id", type=int)
        parser.add_argument(
            "--rapor-tarihi", type=str, default=None,
            help="YYYY-MM-DD formatında rapor tarihi (varsayılan: bugün).",
        )
        parser.add_argument(
            "--mod", choices=["gunluk", "aylik"], default="gunluk",
            help=(
                "gunluk → sadece o günkü vadeli sözleşmeler (IFS günlük mod, varsayılan)\n"
                "aylik  → tüm aktif sözleşmeler (ay sonu tam BDDK bildirimi)"
            ),
        )

    def handle(self, *args, **options):
        rapor_tarihi = None
        if options["rapor_tarihi"]:
            try:
                rapor_tarihi = date.fromisoformat(options["rapor_tarihi"])
            except ValueError as exc:
                raise CommandError(f"Geçersiz tarih formatı: {exc}")

        mod = "daily" if options["mod"] == "gunluk" else "monthly"

        count = run_krs_pipeline(options["company_id"], rapor_tarihi, mod=mod)
        self.stdout.write(self.style.SUCCESS(
            f"{count} sözleşme için KRS hesaplandı "
            f"({'günlük' if mod=='daily' else 'aylık'} mod)."
        ))
