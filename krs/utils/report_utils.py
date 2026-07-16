from django.db.models import QuerySet, Q, Case, When, Value, IntegerField
from django.utils import timezone
from django.conf import settings
from django.core.files.base import ContentFile

from trade.models import TradeTransaction
from companies.models import Company
from leasing.models import Lease
from krs.models import *

from datetime import date, datetime
import io
import os

INSTITUTION_CODE = "0100309309"          # CS0000/CS9999 header'ındaki 10-haneli kurum kodu
INSTITUTION_REF  = INSTITUTION_CODE[2:10]  # sözleşme refansında kullanılan 8 haneli kısım
CURRENCY_CODE    = "19490"               # TRY para birimi kodu
CREDIT_TYPE_CODE = "03112"               # Finansal kiralama sabit türü
ADDRESS_CODE     = "1020000101"          # CS0301'deki sabit adres kodu

def _record(fields: dict[int, str]) -> str:
    """Alanların konumlarını (int) ve değerlerini (str) alıp
    500-karakterlik satır üretir."""
    row = [" "] * 500
    for pos, val in fields.items():
        for i, ch in enumerate(val):
            if pos + i < 500:
                row[pos + i] = ch
    return "".join(row)

def make_cs0000(krs_report):
    return _record({
        0: krs_report.kayit_turu,
        6: krs_report.versiyon,
        8: krs_report.uye_kodu,
        13: krs_report.portfoy_kodu,
        16: " " * 62,
        78: krs_report.uye_adi,
        108: krs_report.olusturma_tarihi,
        116: krs_report.bildirim_tarihi,
        124: " " * 376,
    })

def make_cs0100(krs_report):
    return _record({
        0: krs_report.kayit_turu,
        6: krs_report.versiyon,
        8: krs_report.uye_kodu,
        13: krs_report.portfoy_kodu,
        16: krs_report.portfoy_alt_kodu,
        18: krs_report.hesap_numarasi,
        38: krs_report.sube_kodu,
        46: krs_report.birim_kodu,
        51: krs_report.hesapla_iliskili_kisi_sayisi,
        52: krs_report.doviz_kodu,
        55: krs_report.doviz_boleni,
        56: krs_report.ozel_talimat_gostergesi,
        58: krs_report.acilis_tarihi,
        66: krs_report.basvuru_referans_numarasi,
        86: krs_report.kredi_turu,
        88: krs_report.faiz_orani_gostergesi,
        89: krs_report.kredi_kullanim_amaci,
        91: "            "
    })

def make_cs0200(krs_report):
    return _record({
        0: krs_report.kayit_turu,
        6: krs_report.versiyon,
        8: krs_report.uye_kodu,
        13: krs_report.portfoy_kodu,
        16: krs_report.portfoy_alt_kodu,
        18: krs_report.hesap_numarasi,
        38: krs_report.hesap_sahibinin_numarasi,
        39: krs_report.ozel_talimat_gostergesi,
        41: krs_report.hesap_sahibi_turu,
        42: krs_report.birinci_kimlik_turu,
        43: krs_report.birinci_kimlik_numarasi,
        63: " ",
        64: " " * 20,
        84: " " * 2,
        86: krs_report.uyruk,
        88: " " * 10,
        98: krs_report.soyadi,
        128: " " * 10,
        138: krs_report.ilk_ad_1,
        153: " " * 15,
        168: " " * 30,
        198: " " * 30,
        228: krs_report.anne_adi,
        243: krs_report.baba_adi,
    })




def make_krs_report(company, date):
    company_obj = Company.objects.filter(id = int(company)).first()
    trade_transactions = TradeTransaction.objects.select_related('lease').filter(
        company=company_obj,
        record_date__date=datetime.strptime(date, "%d.%m.%Y").date(),
        posting_group_name__in=["Kira"],
        lease__lease_status__in=["aktiflestirildi"],
        amount_type = '0',
    ).exclude(
        amount = 0,
        local_amount = 0,
    )

    if trade_transactions:
        for tt in trade_transactions:
            print(tt.lease.contract.contract_id)

    print(trade_transactions)

def create_krs_report(company_uuid):
    company = Company.objects.filter(uuid = company_uuid).first()
    leases = Lease.objects.filter(
        Q(company = company) &
        Q(is_last_project=True) &
        # Q(is_last_project_arinet=True) &
        ~Q(lease_status__in=["iptal_edildi","feshedildi","planlandi"]) &
        Q(activation_date=date(2026,7,9))
    )

    print(leases)

    KrsReport.objects.all().delete()

    #başlık kaydı
    KrsReport.objects.create(
        company=company,
        kayit_turu=KayitTuru.CS0000,
        versiyon=Versiyon._01,
        uye_kodu="00309",
        portfoy_kodu="309",
        uye_adi="ARI FİNANSAL KİRALAMA A.Ş.",
        olusturma_tarihi=timezone.now().date().strftime("%Y%m%d"),
        bildirim_tarihi=timezone.now().date().strftime("%Y%m%d")
    )
    
    #satır kaydı
    for lease in leases:
        if lease.currency.code == "TRY":
            doviz_kodu = "949"
        elif lease.currency.code == "USD":
            doviz_kodu = "840"
        elif lease.currency.code == "EUR":
            doviz_kodu = "978"
        else:
            doviz_kodu = "000"

        if lease.activation_date == date(2026,7,9):
            KrsReport.objects.create(
                company=company,
                contract=lease.contract,
                lease=lease,
                kayit_turu=KayitTuru.CS0200,
                versiyon=Versiyon._02,
                uye_kodu="00309",
                portfoy_kodu="309",
                portfoy_alt_kodu="00",
                hesap_numarasi=str(lease.contract.contract_id).ljust(20),
                hesap_sahibinin_numarasi="1",
                ozel_talimat_gostergesi="  ",
                hesap_sahibi_turu=BasvuruSahibiTuru._1,
                birinci_kimlik_turu=KimlikTuru._6,
                birinci_kimlik_numarasi=lease.contract.partner.tc_vkn_no.ljust(20) if lease.contract and lease.contract.partner and lease.contract.partner.tc_vkn_no else " " * 20,
                uyruk=Uyruk._99,
                soyadi=lease.contract.partner.last_name.ljust(20) if lease.contract and lease.contract.partner and lease.contract.partner.last_name else " " * 30,
                ilk_ad_1=lease.contract.partner.first_name.ljust(15) if lease.contract and lease.contract.partner and lease.contract.partner.first_name else " " * 15,
                anne_adi=lease.contract.partner.mother_name.ljust(15) if lease.contract and lease.contract.partner and lease.contract.partner.mother_name else " " * 15,
                baba_adi=lease.contract.partner.father_name.ljust(15) if lease.contract and lease.contract.partner and lease.contract.partner.father_name else " " * 15,
            )

        KrsReport.objects.create(
            company=company,
            contract=lease.contract,
            lease=lease,
            kayit_turu=KayitTuru.CS0100,
            versiyon=Versiyon._01,
            uye_kodu="00309",
            portfoy_kodu="309",
            portfoy_alt_kodu="00",
            hesap_numarasi=str(lease.contract.contract_id).ljust(20),
            sube_kodu="  ",
            birim_kodu="  ",
            hesapla_iliskili_kisi_sayisi="1",
            doviz_kodu=doviz_kodu,
            doviz_boleni="0",
            ozel_talimat_gostergesi="  ",
            acilis_tarihi=lease.activation_date.strftime("%Y%m%d") if lease and lease.activation_date else "00000000",
            basvuru_referans_numarasi="                    ",
            kredi_turu=KrediTuru._03,
            faiz_orani_gostergesi=FaizOraniGostergesi._1,
            kredi_kullanim_amaci=KrediKullanimAmaci._12
        )
        

    buf = io.StringIO()

    krs_reports = KrsReport.objects.filter(company=company).annotate(
        cs0000_first=Case(
            When(kayit_turu=KayitTuru.CS0000, then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        ),
        kayit_turu_sira=Case(
            When(kayit_turu=KayitTuru.CS0200, then=Value(0)),
            When(kayit_turu=KayitTuru.CS0100, then=Value(1)),
            When(kayit_turu=KayitTuru.CS0301, then=Value(2)),
            default=Value(3),
            output_field=IntegerField(),
        ),
    ).order_by("cs0000_first", "hesap_numarasi", "kayit_turu_sira")
    for krs_report in krs_reports:
        if krs_report.kayit_turu == KayitTuru.CS0000:
            buf.write(make_cs0000(krs_report) + "\n")
        elif krs_report.kayit_turu == KayitTuru.CS0100:
            buf.write(make_cs0100(krs_report) + "\n")
        elif krs_report.kayit_turu == KayitTuru.CS0200:
            buf.write(make_cs0200(krs_report) + "\n")

    base_path = os.path.join(os.getcwd(), "media", "docs", str(company.uuid), "krs", "krs_reports")
    if not os.path.exists(base_path):
            os.makedirs(base_path)

    file_path = os.path.join(base_path, f"KrsBildirimi_{timezone.now().date().strftime('%Y%m%d')}_3.txt")
    with open(file_path, "wb") as f:
        f.write(("\ufeff" + buf.getvalue()).encode("utf-8"))

    KrsReportDocument.objects.create(
        company=company,
        label=f"KrsBildirimi_{timezone.now().date().strftime('%Y%m%d')}_3.txt",
        file=ContentFile(open(file_path, "rb").read(), name=f"KrsBildirimi_{timezone.now().date().strftime('%Y%m%d')}_3.txt")
    )