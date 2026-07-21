from django.db.models import QuerySet, Q, Case, When, Value, IntegerField, Sum, OuterRef, Exists
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
from decimal import Decimal, ROUND_HALF_UP

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
        91: " " * 12,
        103: krs_report.teminat_gostergesi,
        104: krs_report.kredi_tutari,
        113: krs_report.depozito_tutari,
        122: krs_report.sozlesme_suresi,
        125: krs_report.odeme_sikligi,
        127: krs_report.taksit_tutari,
        136: krs_report.son_taksit_tutari,
        145: krs_report.taksit_sayisi,
        148: krs_report.odeme_sekli,
        150: " " * 9,
        159: " " * 25,
        184: krs_report.hesap_odeme_durumu,
        185: " " * 1,
        186: krs_report.toplam_borc_bakiyesi,
        195: krs_report.kredi_bakiyesi_gostergesi,
        196: krs_report.borc_faizi_bakiyesi,
        205: krs_report.gecikmedeki_bakiye,
        214: krs_report.vadesinde_yapilmayan_odeme,
        216: krs_report.son_odeme_tutari,
        225: krs_report.son_odeme_tarihi,
        233: krs_report.kapanis_tarihi,
        241: " " * 8,
        249: krs_report.kanuni_takip_tarihi,
        257: krs_report.tahsil_edilme_tarihi,
        265: " " * 2,
        267: krs_report.kapanma_nedeni,
        269: krs_report.hesabin_ozel_durumu,
        270: " " * 1,
        271: krs_report.yeni_hesap_numarasi,
        291: " " * 9,
        300: krs_report.kalan_taksit_bakiyesi,
        309: krs_report.taksit_tarihi_gostergesi,
        310: krs_report.tarihce_duzeltme_gostergesi,
        311: krs_report.yeniden_yapilandirma_gostergesi,
        312: krs_report.yeniden_yapilandirma_tarihi,
        320: krs_report.tedbir_karari_gostergesi,
        321: krs_report.kayittan_dusulen_tutar,
        330: krs_report.nakit_cekim_tutari,
        339: krs_report.gecikme_gun_sayisi,
        341: krs_report.ekstre_odeme_orani,
        344: " " * 156,
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
        258: krs_report.cinsiyet,
        259: " " * 60,
        319: krs_report.dogum_tarihi,
        327: krs_report.dogum_yeri,
        357: " " * 30,
        387: " " * 10,
        397: " ",
        398: " " * 102,
    })

def make_cs0301(krs_report):
    return _record({
        0: krs_report.kayit_turu,
        6: krs_report.versiyon,
        8: krs_report.uye_kodu,
        13: krs_report.portfoy_kodu,
        16: krs_report.portfoy_alt_kodu,
        18: krs_report.hesap_numarasi,
        38: krs_report.hesap_sahibinin_numarasi,
        39: krs_report.ozel_talimat_gostergesi,
        41: krs_report.adres_tipi,
        42: krs_report.simdiki_onceki_adres_gostergesi,
        43: " " * 8,
        51: " " * 8,
        59: " " * 4,
        63: krs_report.satir_1,
        93: krs_report.satir_2,
        123: krs_report.satir_3,
        153: krs_report.satir_4,
        183: " " * 10,
        193: " " * 307,
    })

def make_cs9999(krs_report):
    return _record({
        0: krs_report.kayit_turu,
        6: krs_report.versiyon,
        8: krs_report.uye_kodu,
        13: krs_report.portfoy_kodu,
        16: " " * 62,
        78: krs_report.hesap_kayitlarinin_toplam_sayisi,
        85: krs_report.diger_para_birimine_gore_hesap_kayitlarinin_toplam_sayisi,
        92: krs_report.hesap_gecmisi_kayitlarinin_toplam_sayisi,
        99: krs_report.isim_kayitlarinin_toplam_sayisi,
        106: krs_report.formatlanmamis_adres_kayitlarinin_toplam_sayisi,
        113: krs_report.detayli_kisisel_bilgiler_kayitlarinin_toplam_sayisi,
        120: krs_report.detayli_isveren_bilgileri_kayitlarinin_toplam_sayisi,
        127: krs_report.detayli_banka_bilgileri_kayitlarinin_toplam_sayisi,
        134: " " * 366,
        
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

def create_krs_report(company_uuid,report_date):
    company = Company.objects.filter(uuid = company_uuid).first()

    trade_transactions  = TradeTransaction.objects.select_related('lease').filter(
        lease = OuterRef('pk'),
        due_date = report_date,
    )

    leases = Lease.objects.filter(
        Q(company = company) &
        Q(is_last_project=True) &
        # Q(is_last_project_arinet=True) &
        ~Q(lease_status__in=["iptal_edildi","feshedildi","planlandi"]) &
        (
            Q(activation_date=report_date) |
            Exists(trade_transactions)
            #Q(code='60702/3.1.1')
        )
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
        #para birimi
        if lease.currency.code == "TRY":
            doviz_kodu = "949"
        elif lease.currency.code == "USD":
            doviz_kodu = "840"
        elif lease.currency.code == "EUR":
            doviz_kodu = "978"
        else:
            doviz_kodu = "000"

        #cinsiyet
        if lease.contract and lease.contract.partner and lease.contract.partner.sex:
            if lease.contract.partner.sex == "Bay":
                cinsiyet = Cinsiyet._1
            elif lease.contract.partner.sex == "Bayan":
                cinsiyet = Cinsiyet._2
            else:
                cinsiyet = Cinsiyet._9
        else:
            cinsiyet = Cinsiyet._9

        if lease.contract and lease.contract.partner and lease.contract.partner.address:
            adres = lease.contract.partner.address
            satir1 = adres[0:30].ljust(30)
            satir2 = adres[30:60].ljust(30)
            satir3 = adres[60:90].ljust(30)
            satir4 = adres[90:120].ljust(30)

        if lease.activation_date == report_date: #or lease.code == '60702/3.1.1':
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
                cinsiyet=cinsiyet,
                dogum_tarihi=lease.contract.partner.birthday.strftime("%Y%m%d") if lease.contract and lease.contract.partner and lease.contract.partner.birthday else "99999999",
                dogum_yeri=lease.contract.partner.birth_place.ljust(30) if lease.contract and lease.contract.partner and lease.contract.partner.birth_place else " " * 30,

            )

            KrsReport.objects.create(
                company=company,
                contract=lease.contract,
                lease=lease,
                kayit_turu=KayitTuru.CS0301,
                versiyon=Versiyon._02,
                uye_kodu="00309",
                portfoy_kodu="309",
                portfoy_alt_kodu="00",
                hesap_numarasi=str(lease.contract.contract_id).ljust(20),
                hesap_sahibinin_numarasi="1",
                ozel_talimat_gostergesi="  ",
                adres_tipi=AdresTuru._1,
                simdiki_onceki_adres_gostergesi=SimdikiOncekiAdresKodu._0,
                adrese_tasindigi_tarih="99999999",
                adresten_ayrildigi_tarih="99999999",
                satir_1=satir1,
                satir_2=satir2,
                satir_3=satir3,
                satir_4=satir4
            )

        #kredi tutarı
        if lease.operasyon_baz_maliyet <= Decimal("2.00"):
            old_lease = Lease.objects.filter(
                ~Q(lease_id=lease.lease_id) &
                Q(main_lease_id=lease.main_lease_id) &
                Q(lease_status__in=["baskasina_transfer_edildi"]) &
                Q(operasyon_baz_maliyet__gt=Decimal("2.00"))
            ).order_by("-lease_id").first()
            kredi_tutari = old_lease.operasyon_baz_maliyet if old_lease else lease.operasyon_baz_maliyet
        elif "/" in lease.code:
            cleaned_code = lease.code.split("/")[0] + ".1.1"
            old_lease = Lease.objects.filter(
                code=cleaned_code
            ).first()
            if not old_lease:
                cleaned_code = lease.code.split("/")[0] + ".1.0"
                old_lease = Lease.objects.filter(
                code=cleaned_code
            ).first()
            kredi_tutari = old_lease.operasyon_baz_maliyet if old_lease else lease.operasyon_baz_maliyet
        else:
            kredi_tutari = lease.operasyon_baz_maliyet

        #peşinat
        installment = lease.lease_installments.filter(type='2').first()
        depozito_tutari = installment.payment if installment else Decimal("0.00")

        #taksit
        last_installment = lease.lease_installments.filter(type='1').order_by("-sequency").first()
        taksit_tutari = last_installment.payment if last_installment else Decimal("0.00")

        #son taksit
        last2_installment = lease.lease_installments.filter(type='1', payment_date__lt=datetime.now().date()).order_by("-sequency").first()
        taksit_tutari = last2_installment.payment if last2_installment else Decimal("0.00")

        #gecikme
        if lease.overdue_days > 0:
            overdue_start_date = datetime.now().date() - timezone.timedelta(days=lease.overdue_days)
            overdue_installments_count = lease.lease_installments.filter(type='1', payment_date__gte=overdue_start_date, payment_date__lt=datetime.now().date()).count()
            if overdue_installments_count == 1:
                hesap_odeme_durumu = HesapOdemeDurumu._1
            elif overdue_installments_count == 2:
                hesap_odeme_durumu = HesapOdemeDurumu._2
            elif overdue_installments_count == 3:
                hesap_odeme_durumu = HesapOdemeDurumu._3
            elif overdue_installments_count == 4:
                hesap_odeme_durumu = HesapOdemeDurumu._4
            elif overdue_installments_count == 5:
                hesap_odeme_durumu = HesapOdemeDurumu._5
            elif overdue_installments_count == 6:
                hesap_odeme_durumu = HesapOdemeDurumu._6
            elif overdue_installments_count > 6:
                hesap_odeme_durumu = HesapOdemeDurumu._6
        else:
            hesap_odeme_durumu = HesapOdemeDurumu._0

        #toplam borc
        next_installments_total = lease.lease_installments.filter(type='1', payment_date__gte=datetime.now().date()).aggregate(total=Sum('principal'))['total'] or Decimal("0.00")
        toplam_borc_bakiyesi = (lease.overdue_amount) + next_installments_total
        if toplam_borc_bakiyesi < 0:
            toplam_borc_bakiyesi = abs(toplam_borc_bakiyesi)
            kredi_bakiyesi_gostergesi = KrediBakiyesiGostergesi._1
        else:
            kredi_bakiyesi_gostergesi = KrediBakiyesiGostergesi._0

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
            acilis_tarihi=lease.activation_date.strftime("%Y%m%d") if lease and lease.activation_date else "99999999",
            basvuru_referans_numarasi="                    ",
            kredi_turu=KrediTuru._03,
            faiz_orani_gostergesi=FaizOraniGostergesi._1,
            kredi_kullanim_amaci=KrediKullanimAmaci._12,
            teminat_gostergesi = TeminatGostergesi._0,
            kredi_tutari=str(int(kredi_tutari.quantize(Decimal("1"), rounding=ROUND_HALF_UP))).rjust(9, "0") if lease else "000000000",
            depozito_tutari=str(int(depozito_tutari.quantize(Decimal("1"), rounding=ROUND_HALF_UP))).rjust(9, "0") if lease else "000000000",
            sozlesme_suresi=str(lease.vade).rjust(3, "0") if lease else "000",
            odeme_sikligi="01",
            taksit_tutari=str(int(taksit_tutari.quantize(Decimal("1"), rounding=ROUND_HALF_UP))).rjust(9, "0") if lease else "000000000",
            son_taksit_tutari=str(int(taksit_tutari.quantize(Decimal("1"), rounding=ROUND_HALF_UP))).rjust(9, "0") if lease else "000000000",
            taksit_sayisi=str(lease.vade).rjust(3, "0") if lease else "000",
            odeme_sekli=OdemeSekli._04,
            hesap_odeme_durumu=hesap_odeme_durumu,
            toplam_borc_bakiyesi=str(int(toplam_borc_bakiyesi.quantize(Decimal("1"), rounding=ROUND_HALF_UP))).rjust(9, "0") if lease else "000000000",
            kredi_bakiyesi_gostergesi=kredi_bakiyesi_gostergesi,
            borc_faizi_bakiyesi = " " * 9,
            gecikmedeki_bakiye = str(int(lease.overdue_amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))).rjust(9, "0") if lease else "000000000",
            vadesinde_yapilmayan_odeme = " " * 2, #tekrar bakılacak
            son_odeme_tutari = " " * 9, #tekrar bakılacak
            son_odeme_tarihi = " " * 8, #tekrar bakılacak
            kapanis_tarihi = " " * 8, #tekrar bakılacak
            kanuni_takip_tarihi = " " * 8, #tekrar bakılacak
            tahsil_edilme_tarihi = " " * 8, #tekrar bakılacak
            kapanma_nedeni = " " * 2, #tekrar bakılacak
            hesabin_ozel_durumu = " " * 1, #tekrar bakılacak
            yeni_hesap_numarasi = " " * 20, #tekrar bakılacak
            kalan_taksit_bakiyesi = str(int(next_installments_total.quantize(Decimal("1"), rounding=ROUND_HALF_UP))).rjust(9, "0") if lease else "000000000",
            taksit_tarihi_gostergesi = " " * 1, #tekrar bakılacak
            tarihce_duzeltme_gostergesi = TarihceDuzeltmeGostergesi._0,
            yeniden_yapilandirma_gostergesi = " " * 1, #tekrar bakılacak
            yeniden_yapilandirma_tarihi = " " * 8, #tekrar bakılacak
            tedbir_karari_gostergesi = TedbirKarariGostergesi._,
            kayittan_dusulen_tutar = "000000000", #tekrar bakılacak
            nakit_cekim_tutari = " " * 9, #tekrar bakılacak
            gecikme_gun_sayisi = str(lease.overdue_days).rjust(2, "0") if lease else "00",
            ekstre_odeme_orani = " " * 3
        )
        
    #bitiş kaydı
    KrsReport.objects.create(
        company=company,
        kayit_turu=KayitTuru.CS9999,
        versiyon=Versiyon._01,
        uye_kodu="00309",
        portfoy_kodu="309",
        hesap_kayitlarinin_toplam_sayisi=str(KrsReport.objects.select_related("company").filter(company=company,kayit_turu=KayitTuru.CS0100).count()).rjust(7, "0"),
        diger_para_birimine_gore_hesap_kayitlarinin_toplam_sayisi="0000000",
        hesap_gecmisi_kayitlarinin_toplam_sayisi="0000000",
        isim_kayitlarinin_toplam_sayisi=str(KrsReport.objects.select_related("company").filter(company=company,kayit_turu=KayitTuru.CS0200).count()).rjust(7, "0"),
        formatlanmamis_adres_kayitlarinin_toplam_sayisi=str(KrsReport.objects.select_related("company").filter(company=company,kayit_turu=KayitTuru.CS0301).count()).rjust(7, "0"),
        detayli_kisisel_bilgiler_kayitlarinin_toplam_sayisi="0000000",
        detayli_isveren_bilgileri_kayitlarinin_toplam_sayisi="0000000",
        detayli_banka_bilgileri_kayitlarinin_toplam_sayisi="0000000",
    )

    buf = io.StringIO()

    krs_reports = KrsReport.objects.filter(company=company).annotate(
        cs0000_first=Case(
            When(kayit_turu=KayitTuru.CS0000, then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        ),
        kayit_turu_sira=Case(
            When(kayit_turu=KayitTuru.CS0100, then=Value(0)),
            When(kayit_turu=KayitTuru.CS0200, then=Value(1)),
            When(kayit_turu=KayitTuru.CS0301, then=Value(2)),
            default=Value(3),
            output_field=IntegerField(),
        ),
        cs9999_last=Case(
            When(kayit_turu=KayitTuru.CS9999, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        ),
    ).order_by("cs0000_first", "hesap_numarasi", "kayit_turu_sira", "cs9999_last")
    for krs_report in krs_reports:
        if krs_report.kayit_turu == KayitTuru.CS0000:
            buf.write(make_cs0000(krs_report) + "\n")
        elif krs_report.kayit_turu == KayitTuru.CS0100:
            buf.write(make_cs0100(krs_report) + "\n")
        elif krs_report.kayit_turu == KayitTuru.CS0200:
            buf.write(make_cs0200(krs_report) + "\n")
        elif krs_report.kayit_turu == KayitTuru.CS0301:
            buf.write(make_cs0301(krs_report) + "\n")
        elif krs_report.kayit_turu == KayitTuru.CS9999:
            buf.write(make_cs9999(krs_report) + "\n")

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