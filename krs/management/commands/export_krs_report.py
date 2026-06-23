"""
Kullanım:
    python manage.py export_krs_report 2
    python manage.py export_krs_report 2 --rapor-tarihi 2026-06-22
    python manage.py export_krs_report 2 --cikti /tmp/KrsBildirimi_20260622.txt

Dosya IFS'in ürettiği 'KrsBildirimi_YYMMDD-HHMMSS.txt' formatıyla aynı
yapıda, UTF-8 BOM kodlamasıyla üretilir.
"""

import os
from datetime import date

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from krs.services.report_generator import (
    ContractKrsData,
    generate_report,
)
from krs import models as krs_models


def _rapor_tarihi_or_today(s):
    if not s:
        return date.today()
    try:
        return date.fromisoformat(s)
    except ValueError as exc:
        raise CommandError(f"Geçersiz tarih formatı: {exc}")


class Command(BaseCommand):
    help = "KRS bildirim dosyasını üretir (IFS / BDDK formatı, UTF-8 BOM)."

    def add_arguments(self, parser):
        parser.add_argument("company_id", type=int)
        parser.add_argument(
            "--rapor-tarihi", type=str, default=None,
            help="YYYY-MM-DD formatında rapor tarihi, verilmezse bugün kullanılır.",
        )
        parser.add_argument(
            "--cikti", type=str, default=None,
            help="Çıktı dosyasının tam yolu. Verilmezse BASE_DIR altında oluşturulur.",
        )

    def handle(self, *args, **options):
        company_id = options["company_id"]
        rapor_tarihi = _rapor_tarihi_or_today(options["rapor_tarihi"])

        # Company bilgisi
        from common.models import Company  # TODO: projenize göre düzeltin
        try:
            company = Company.objects.get(pk=company_id)
        except Company.DoesNotExist:
            raise CommandError(f"Company {company_id} bulunamadı.")

        # KrsTemerrutHavuz'dan bu rapor tarihi için verileri çek
        havuz_qs = krs_models.KrsTemerrutHavuz.objects.filter(
            company_id=company_id,
            rapor_tarihi=rapor_tarihi,
        ).order_by("contract_header_id")

        if not havuz_qs.exists():
            raise CommandError(
                f"Company {company_id} için {rapor_tarihi} tarihli KRS verisi bulunamadı.\n"
                f"Önce `python manage.py run_krs_pipeline {company_id}` çalıştırın."
            )

        # ---- Sözleşme + Partner verisini çek ----
        # KrsTemerrutHavuz.contract_header_id ↔ Lease.lease_id eşleşmesini
        # Contract modelinize göre düzenleyin.  Şu an basit bir JOIN yapılıyor;
        # Lease modelindeki hangi alanın ContractHeaderId'ye karşılık geldiği
        # netleştiğinde bu bölümü güncelleyin (bkz. models.py TODO).
        #
        # TODO: Lease / Contract FK bağlantısı kurulunca aşağıyı güncelleyin.
        from leasing.models import Lease       # TODO: gerçek import yolu
        from partners.models import Partner   # TODO: gerçek import yolu

        lease_by_cid = {
            int(l.lease_id): l
            for l in Lease.objects.filter(company_id=company_id)
            if l.lease_id and l.lease_id.isdigit()
        }

        # Yeni sözleşme eşiği: aynı ay içinde aktifleşen sözleşmeler CS010002 olarak gönderilir
        yeni_esigi = rapor_tarihi.replace(day=1)

        contracts = []
        for h in havuz_qs:
            lease = lease_by_cid.get(h.contract_header_id)
            partner = lease.contract.partner if lease and lease.contract_id else None
            ref_date = (
                lease.activation_date or lease.signature_date
                if lease else rapor_tarihi
            )
            is_new = bool(ref_date and ref_date >= yeni_esigi)

            c = ContractKrsData(
                contract_header_id=h.contract_header_id,
                reference_date=ref_date or rapor_tarihi,
                is_new=is_new,
                risk_grubu=_risk_grubu_int(h.risk_grubu),
                toplam_acik_bakiye=h.toplam_acik_bakiye,
                # Lease model alanları — TODO doğrulama gerekiyor
                total_payment=lease.total_payment if lease else h.toplam_acik_bakiye,
                kalan_anapara=(lease.total_payment - lease.paid_amount) if lease else h.toplam_acik_bakiye,
                gecikme_faizi=h.toplam_bugune_kadar_temerrut,
                aylik_taksit=lease.installment_amount if lease else h.toplam_acik_bakiye,
                teminat_kodu="104",   # TODO: Lease modelinden belirleyin
                # Partner (müşteri) bilgileri
                tc_no=partner.tc_no if partner else "",
                soyadi=partner.last_name if partner else "",
                adi=partner.first_name if partner else "",
                anne_adi=getattr(partner, "anne_adi", "") if partner else "",  # Partner'da varsa
                baba_adi=partner.father_name if partner else "",
                dogum_tarihi=partner.birthday if partner else None,
                adres=_format_adres(partner) if partner else "",
            )
            contracts.append(c)

        # ---- Raporu üret ----
        #company_name = getattr(company, "name", str(company))
        company_name = "ARI FİNANSAL KİRALAMA A.Ş." if company.pk == 2 else company_name
        report_bytes = generate_report(
            contracts=contracts,
            company_name=company_name,
            period_start=rapor_tarihi,
            period_end=rapor_tarihi,
        )

        # ---- Dosyaya yaz ----
        out_path = options["cikti"] or os.path.join(
            settings.BASE_DIR,
            f"KrsBildirimi_{rapor_tarihi.strftime('%y%m%d')}.txt",
        )
        with open(out_path, "wb") as f:
            f.write(report_bytes)

        self.stdout.write(self.style.SUCCESS(
            f"{len(contracts)} sözleşme → {out_path} ({len(report_bytes):,} bayt)"
        ))


def _risk_grubu_int(risk_grubu_str):
    """RiskGrubu TextChoices string'ini int'e çevirir."""
    mapping = {
        "grup_1": 1, "grup_2": 2, "grup_3": 3, "grup_4": 4, "grup_5": 5,
    }
    return mapping.get(risk_grubu_str or "", 0)


def _format_adres(partner) -> str:
    """Partner modelinden tek satır adres üretir."""
    parts = []
    if getattr(partner, "address", ""):
        parts.append(partner.address)
    city_name = ""
    if getattr(partner, "city", None):
        city_name = str(partner.city)
        parts.append(city_name)
    if getattr(partner, "country", None):
        country_str = str(partner.country)
        if country_str != "TÜRKİYE" and country_str != "TR":
            parts.append(country_str)
    return "  ".join(p.strip() for p in parts if p.strip())
