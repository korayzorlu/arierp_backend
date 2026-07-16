"""
krs/models.py

IFS/Oracle tarafındaki TRLEAS_KAPAMA_TAB, TRLEAS_KAPAMA_DETAY_TAB ve
trleas_temerrut_havuz_tab'ın Django/PostgreSQL karşılıkları.

TODO (entegrasyon): Aşağıdaki `Company` import'unu kendi projenizdeki
gerçek modül yoluna göre düzeltin (Lease/Contract modelleriniz hangi
app'teyse muhtemelen oradan import edilmeli).
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid

# TODO: gerçek import yolunuza göre düzeltin, örn:
#   from common.models import Company
from common.models import Company  # noqa: F401
from contracts.models import Contract
from leasing.models import Lease

class KayitTuru(models.TextChoices):
    CS0000 = 'CS0000', 'Başlık kaydı'
    CS0100 = 'CS0100', 'Hesap kayıtları'
    CS0199 = 'CS0199', 'Hesap geçmişi kaydı(Sadece ilk toplu bildirimde)'
    CS0200 = 'CS0200', 'İsim kayıtları'
    CS0301 = 'CS0301', 'Formatlanmamış adres kayıtları'
    CS0400 = 'CS0400', 'Kişisel Bilgilere ilişkin kayıtlar'
    CS0500 = 'CS0500', 'İşveren Bilgilerine İlişkin kayıtlar'
    CS0600 = 'CS0600', 'Banka Bilgilerine İlişkin kayıtları'
    CS9999 = 'CS9999', 'Bitiş kaydı'

class Versiyon(models.TextChoices):
    _01 = '01', 'Finansal değişim'
    _02 = '02', 'Yeni hesap açılışı'
    _03 = '03', 'Ekkart, kefil, müşterek borçlu veya özlük, adres ve iletişim bilgileri bildirimi'

class KrediTuru(models.TextChoices):
    _02 = '02', 'Tüketici kredisi'
    _03 = '03', 'Ev kredisi'
    _23 = '23', 'Kredi kartı'
    _26 = '26', 'Kredili mevduat'
    _50 = '50', 'Mevcut bireysel müşteri'
    _60 = '60', 'Mevcut kurumsal müşteri'
    _70 = '70', 'Portföy yönetimi'
    _61 = '61', 'Kurumsal kredi başvurusu'
    _90 = '90', 'Başvurunun yeniden sorgulanması'

class FaizOraniGostergesi(models.TextChoices):
    _1 = '1', 'Sabit Faiz'
    _2 = '2', 'Değişken Faiz'
    _3 = '8', 'Diğer'
    _4 = '9', 'Bilinmiyor'

class KrediKullanimAmaci(models.TextChoices):
    _01 = '01', 'Yeni Otomobil'
    _02 = '02', 'Eski Otomobil'
    _03 = '03', 'Kamyon, Otobüs, Tır, Traktör, Ticari Araç'
    _04 = '04', 'Motorsiklet'
    _05 = '05', 'Diğer Kara Aracı'
    _06 = '06', 'Ev Eşyası (Mobilya, halı vb.)'
    _07 = '07', 'Elektronik Eşya (TV, video, müzik seti vb.)'
    _08 = '08', 'Beyaz Eşya (Buzdolabı, çamaşır makinası vb.)'
    _09 = '09', 'Giyim'
    _10 = '10', 'Seyahat'
    _11 = '11', 'Deniz Aracı'
    _12 = '12', 'Konut'
    _13 = '13', 'Borç Ödemesi'
    _14 = '14', 'Çeyiz/Evlilik'
    _15 = '15', 'Eğitim'
    _16 = '16', 'Bilgisayar'
    _17 = '17', 'Tadilat, Dekorasyon'
    _18 = '18', 'Kooperatif Ödemesi, Kira, Depozito'
    _19 = '19', 'Yatırım – Menkul Değer Alımı'
    _20 = '20', 'Sağlık'
    _21 = '21', 'Ticari Amaçlı'
    _22 = '22', 'Hobi'
    _98 = '98', 'Diğer'
    _99 = '99', 'Bilinmiyor'

class TeminatGostergesi(models.TextChoices):
    _0 = '0', 'Teminatsız'
    _1 = '1', 'Rehin'
    _2 = '2', 'Teminat/İpotek'
    _3 = '3', 'Şirket kefaleti'
    _4 = '4', 'Şahıs kefaleti'
    _8 = '8', 'Diğer teminat'
    _9 = '9', 'Bilinmiyor'

class OdemeSikligi(models.TextChoices):
    _00 = '00', 'Haftalık'
    _01 = '01', 'Aylık'
    _02 = '02', '2 ayda bir ödeme'
    _03 = '03', '3 ayda bir ödeme'
    _04 = '04', '4 ayda bir ödeme'
    _06 = '06', '6 ayda bir ödeme'
    _12 = '12', 'Yıllık'
    _Nn = 'Nn', 'Her "nn" ayda bir ödeme'
    _98 = '98', 'Değişken'
    _99 = '99', 'Bilinmiyor'

class OdemeSekli(models.TextChoices):
    _01 = '01', 'Özel Ödeme Şekli'
    _02 = '02', 'Değişken Ödeme (Overdraft/Kredi Kartı)'
    _03 = '03', 'Tahsilat öncesi müşteriyi bilgilendirme'
    _04 = '04', 'Senet'
    _05 = '05', 'Sabit Ödeme (Bireysel, Konut, ... )'
    _06 = '06', 'Nakit'
    _07 = '07', 'Banka Çeki'
    _08 = '08', 'Kredi Kartı'
    _98 = '98', 'Diğer'
    _99 = '99', 'Bilinmiyor'

class HesapOdemeDurumu(models.TextChoices):
    _0 = '0', 'Gecikme yok'
    _1 = '1', '1 ödeme gecikmiş durumda'
    _2 = '2', '2 ödeme gecikmiş durumda'
    _3 = '3', '3 ödeme gecikmiş durumda'
    _4 = '4', '4 ödeme gecikmiş durumda'
    _5 = '5', '5 ödeme gecikmiş durumda'
    _6 = '6', '6 ödeme gecikmiş durumda'
    _8 = '8', 'İdari Takip (bu kod sadece sorgu çıktısında paylaşılır, bildirimde kabul edilmez)'
    _D = 'D', 'Hareketsiz Hesap (bu kod sistem tarafından üretilir)'
    _L = 'L', 'Kanuni Takip'
    _U = 'U', 'Sınıflandırılmamış'
    _X = 'X', 'Bilgi gelmedi, güncelleme yapılmadı (bu kod sistem tarafından üretilir)'

class KrediBakiyesiGostergesi(models.TextChoices):
    _0 = '0', 'Borç Bakiyesi'
    _1 = '1', 'Alacak Bakiyesi'

class KapanmaNedeni(models.TextChoices):
    _01 = '01', 'Çözümlenememiş anlaşmazlık'
    _02 = '02', 'Geç ödeme alışkanlığı'
    _03 = '03', 'Müşterinin ödeme güçlüğü çekmesi'
    _04 = '04', 'Müşteriye erişilememiş'
    _05 = '05', 'Müşteri işsiz kalmış'
    _06 = '06', 'Müşteri sakat kalmış'
    _07 = '07', 'Malların el değiştirmesi'
    _08 = '08', 'Vefat etmiş'
    _09 = '09', 'Kayıp, çalıntı kredi kartı'
    _10 = '10', 'Kredi kartının müşteri tarafından iadesi'
    _11 = '11', 'Kredi kartının banka tarafından kapatılması'
    _12 = '12', 'Dolandırıcılık'
    _13 = '13', 'Potansiyel risk'
    _98 = '98', 'Diğer'
    _99 = '99', 'Bilinmiyor'

class HesabinOzelDurumu(models.TextChoices):
    _1 = '1', 'Zarara atıldı'
    _2 = '2', 'Vefat'
    _3 = '3', 'Taşınmış'
    _4 = '4', 'Tartışmalı'
    _5 = '5', 'Banka ile düzenleme yapılmış'
    _6 = '6', 'Müşteri İtirazı'
    _7 = '7', 'Varlık Yönetim Şirketine devir'
    _0 = '0', 'Özel durumu yok'

class TaksitTarihiGostergesi(models.TextChoices):
    _1 = '1', 'Kredinin son ödeme tarihi olduğu göstergesi. Tüketici Kredileri ve Konut kredisi için geçerlidir'

class YenidenYapilandirmaGostergesi(models.TextChoices):
    _ = ' ', 'Hiç yapılandırılmamış hesap'
    _1 = '1', 'Donuk alacaklardan yeniden yapılandırılan hesap'
    _2 = '2', 'Canlı alacaklardan yeniden yapılandırılan hesap'
    _3 = '3', 'Donuk alacaklardan yeniden sınıflandırılan hesap'

class TedbirKarariGostergesi(models.TextChoices):
    _ = ' ', 'Mahkeme tarafından verilen kredi ödemelerinin durdurulmasına yönelik hiç bir tedbir kararı bulunmuyor.'
    _1 = '1', 'Mahkeme tarafından kredi ödemelerinin durdurulmasına yönelik verilen tedbir kararı bulunuyor.'

class BasvuruSahibiTuru(models.TextChoices):
    _1 = '1', 'Esas'
    _2 = '2', 'Müşterek Borçlu'
    _3 = '3', 'Kefil'
    _4 = '4', 'Diğer Teminatın Sahibi'
    _5 = '5', 'Ek kart kullanıcısı'
    _8 = '8', 'Diğer'
    _9 = '9', 'Bilinmiyor'

class KimlikTuru(models.TextChoices):
    _1 = '1', 'Pasaport'
    _2 = '2', 'Sürücü Belgesi'
    _3 = '3', 'Nüfus Cüzdanı'
    _4 = '4', 'Ayrılmış Alan'
    _5 = '5', 'Vergi Numarası'
    _6 = '6', 'TC Kimlik Numarası / Yabancı Kimlik Numarası'
    _7 = '7', 'KKTC Kimlik No'
    _8 = '8', 'Diğer'
    _9 = '9', 'Bilinmiyor'

class Uyruk(models.TextChoices):
    _01 = '01', 'İngiltere'
    _02 = '02', 'Almanya'
    _03 = '03', 'Fransa'
    _04 = '04', 'İtalya'
    _05 = '05', 'İspanya'
    _06 = '06', 'Hollanda'
    _07 = '07', 'Yunanistan'
    _08 = '08', 'Türkiye'
    _09 = '09', 'KKTC'
    _21 = '21', 'Güney Afrika Cumhuriyeti'
    _41 = '41', 'Amerika Birleşik Devletleri'
    _42 = '42', 'Kanada'
    _43 = '43', 'Meksika'
    _44 = '44', 'Orta Amerika'
    _45 = '45', 'Güney Amerika'
    _61 = '61', 'Hindistan'
    _62 = '62', 'Iran'
    _63 = '63', 'Irak'
    _64 = '64', 'Çin'
    _65 = '65', 'Japonya'
    _81 = '81', 'Avusturalya'
    _98 = '98', 'Diğer'
    _99 = '99', 'Bilinmeyen'

class Cinsiyet(models.TextChoices):
    ERKEK = '1', 'Erkek'
    KADIN = '2', 'Kadın'

class RiskGrubu(models.TextChoices):
    """
    !!! YER TUTUCU SINIFLANDIRMA !!!
    TRLEAS_KRS_API / TRLEAS_KRM_API'nin gerçek grup tanımları/etiketleri
    elinize geçtiğinde bu choices'ı ve services/kapama.py::classify_risk_group()
    fonksiyonunu güncelleyin. Şu anki 5 grup, BDDK'nın finansal kiralama
    şirketleri için genel olarak kullandığı yapıya BENZER bir varsayımdır,
    doğrulanmış/onaylanmış bir kaynağa dayanmaz.
    """

    GRUP_1 = "grup_1", _("Grup I - Standart")
    GRUP_2 = "grup_2", _("Grup II - Yakın İzleme")
    GRUP_3 = "grup_3", _("Grup III - Tahsil İmkanı Sınırlı")
    GRUP_4 = "grup_4", _("Grup IV - Tahsili Şüpheli")
    GRUP_5 = "grup_5", _("Grup V - Zarar")


class KapamaHareketi(models.Model):
    """TRLEAS_KAPAMA_TAB karşılığı: sözleşme + tarih bazında fatura/ödeme/
    kapatma/temerrüt durumu. Her pipeline çalışmasında o şirket için
    sıfırdan yeniden üretilir (orijinal PL/SQL'deki "DELETE + yeniden
    INSERT" yaklaşımıyla aynı mantık)."""

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="krs_kapama_hareketleri"
    )
    contract_header_id = models.BigIntegerField(db_index=True)
    tarih = models.DateField()

    fatura_tutar = models.DecimalField(_("Fatura Tutarı"), max_digits=14, decimal_places=2, default=0)
    odeme_tutar = models.DecimalField(_("Ödeme Tutarı"), max_digits=14, decimal_places=2, default=0)
    kapatilan_fatura_tutar = models.DecimalField(_("Kapatılan Fatura Tutarı"), max_digits=14, decimal_places=2, default=0)
    temerrut_tutar = models.DecimalField(_("Temerrüt Tutarı"), max_digits=14, decimal_places=2, default=0)
    bugune_kadar_temerrut = models.DecimalField(_("Bugüne Kadar Temerrüt"), max_digits=14, decimal_places=2, default=0)
    odenmis_temerrut = models.DecimalField(_("Ödenmiş Temerrüt"), max_digits=14, decimal_places=2, default=0)
    gercek_odeme_tutar = models.DecimalField(_("Gerçek Ödeme Tutarı"), max_digits=14, decimal_places=2, default=0)
    protokol = models.DecimalField(_("Protokol"), max_digits=14, decimal_places=2, default=0)

    sentetik = models.BooleanField(
        _("Sentetik"), default=False,
        help_text=_("Fazla ödeme nedeniyle FIFO algoritması tarafından otomatik oluşturulan satır mı"),
    )

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("KRS Kapama Hareketi")
        verbose_name_plural = _("KRS Kapama Hareketleri")
        indexes = [models.Index(fields=["company", "contract_header_id", "tarih"])]
        ordering = ["contract_header_id", "tarih"]

    def __str__(self):
        return f"{self.contract_header_id} / {self.tarih}"


class KapamaDetay(models.Model):
    """TRLEAS_KAPAMA_DETAY_TAB karşılığı: hangi ödeme hangi faturayı ne
    kadar kapattı (FIFO eşleştirme detayı)."""

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="krs_kapama_detaylari"
    )
    contract_header_id = models.BigIntegerField(db_index=True)
    odeme_tarihi = models.DateField(_("Ödeme Tarihi"))
    fatura_tarihi = models.DateField(_("Fatura Tarihi"))
    kapatilan_tutar = models.DecimalField(_("Kapatılan Tutar"), max_digits=14, decimal_places=2)

    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("KRS Kapama Detayı")
        verbose_name_plural = _("KRS Kapama Detayları")
        indexes = [models.Index(fields=["company", "contract_header_id"])]
        ordering = ["contract_header_id", "fatura_tarihi"]

    def __str__(self):
        return f"{self.contract_header_id}: {self.fatura_tarihi} -> {self.odeme_tarihi}"


class KrsTemerrutHavuz(models.Model):
    """
    TRLEAS_UTIL_API.Temerrut_Havuzu'nun ürettiği snapshot'ın karşılığı:
    rapor tarihine göre sözleşme bazlı KRS sonucu. Asıl "KRS raporu" budur;
    geçmiş rapor tarihleri silinmez, her tarih için ayrı satır tutulur
    (orijinal PL/SQL'deki "DELETE WHERE rapor_tarihi=... + INSERT" mantığı).
    """

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="krs_temerrut_havuzu"
    )
    contract_header_id = models.BigIntegerField(db_index=True)
    rapor_tarihi = models.DateField(_("Rapor Tarihi"), db_index=True)

    en_eski_acik_fatura_tarihi = models.DateField(_("En Eski Açık Fatura Tarihi"), null=True, blank=True)
    en_eski_acik_fatura_gecikme_gun = models.IntegerField(_("Gecikme Gün Sayısı"), default=0)
    toplam_acik_bakiye = models.DecimalField(_("Toplam Açık Bakiye"), max_digits=14, decimal_places=2, default=0)
    toplam_bugune_kadar_temerrut = models.DecimalField(_("Toplam Bugüne Kadar Temerrüt"), max_digits=14, decimal_places=2, default=0)

    risk_grubu = models.CharField(
        _("Risk Grubu"), max_length=10, choices=RiskGrubu.choices, null=True, blank=True
    )

    # TODO (opsiyonel): Bu satırı gerçek Lease modelinize bağlamak isterseniz
    # aşağıdaki gibi nullable bir FK ekleyip pipeline.py'de bir eşleştirme
    # adımı (örn. contract_header_id <-> Lease.lease_id/main_lease_id)
    # yazabilirsiniz. Hangi alanın karşılık geldiğini netleştiremediğimiz
    # için bilerek eklenmedi:
    # lease = models.ForeignKey(
    #     "leases.Lease", null=True, blank=True,
    #     on_delete=models.SET_NULL, related_name="krs_sonuclari",
    # )

    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("KRS Raporu")
        verbose_name_plural = _("KRS Raporları")
        constraints = [
            models.UniqueConstraint(
                fields=["company", "contract_header_id", "rapor_tarihi"],
                name="unique_krs_contract_per_report_date",
            )
        ]
        ordering = ["-rapor_tarihi", "contract_header_id"]

    def __str__(self):
        return f"{self.contract_header_id} / {self.rapor_tarihi} / {self.risk_grubu}"

class KrsReport(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="krs_reports")
    
    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name="lease_krs_reports",blank=True, null=True)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="contract_krs_reports",blank=True, null=True)

    kayit_turu = models.CharField(_("Kayıt Türü"), max_length=25, choices=KayitTuru.choices, blank=True, null=True)
    versiyon = models.CharField(_("Versiyon"), max_length=25, choices=Versiyon.choices, blank=True, null=True)
    uye_kodu = models.CharField(_("Üye Kodu"), max_length=5, null=True, blank=True)
    portfoy_kodu = models.CharField(_("Portföy Kodu"), max_length=3, null=True, blank=True)
    portfoy_alt_kodu = models.CharField(_("Portföy Alt Kodu"), max_length=2, null=True, blank=True)

    uye_adi = models.CharField(_("Üye Adı"), max_length=30, null=True, blank=True)
    olusturma_tarihi = models.CharField(_("Oluşturma Tarihi"), max_length=8, null=True, blank=True)
    bildirim_tarihi = models.CharField(_("Bildirim Tarihi"), max_length=8, null=True, blank=True)

    #CS0200 özel alanlar
    hesap_sahibinin_numarasi = models.CharField(_("Hesap Sahibinin Numarası"), max_length=1, null=True, blank=True)
    hesap_sahibi_turu = models.CharField(_("Hesap Sahibi Türü"), max_length=25, choices=BasvuruSahibiTuru.choices, blank=True, null=True)
    birinci_kimlik_turu = models.CharField(_("Birinci Kimlik Türü"), max_length=25, choices=KimlikTuru.choices, blank=True, null=True)
    birinci_kimlik_numarasi = models.CharField(_("Birinci Kimlik Numarası"), max_length=20, null=True, blank=True)
    ikinci_kimlik_turu = models.CharField(_("İkinci Kimlik Türü"), max_length=25, choices=KimlikTuru.choices, blank=True, null=True)
    ikinci_kimlik_numarasi = models.CharField(_("İkinci Kimlik Numarası"), max_length=20, null=True, blank=True)
    uyruk = models.CharField(_("Uyruk"), max_length=2, choices=Uyruk.choices, blank=True, null=True)
    soyadi = models.CharField(_("Soyadı"), max_length=30, null=True, blank=True)
    soyadi_eki = models.CharField(_("Soyadı Eki"), max_length=10, null=True, blank=True)
    ilk_ad_1 = models.CharField(_("İlk Ad 1"), max_length=15, null=True, blank=True)
    ilk_ad_2 = models.CharField(_("İlk Ad 2"), max_length=15, null=True, blank=True)
    anne_adi = models.CharField(_("Anne Adı"), max_length=15, null=True, blank=True)
    baba_adi = models.CharField(_("Baba Adı"), max_length=15, null=True, blank=True)
    cinsiyet = models.CharField(_("Cinsiyet"), max_length=1, choices=Cinsiyet.choices, blank=True, null=True)

    hesap_numarasi = models.CharField(_("Hesap Numarası"), max_length=20, null=True, blank=True)
    sube_kodu = models.CharField(_("Şube Kodu"), max_length=8, null=True, blank=True)
    birim_kodu = models.CharField(_("Birim Kodu"), max_length=5, null=True, blank=True)
    hesapla_iliskili_kisi_sayisi = models.CharField(_("Hesapla İlişkili Kişi Sayısı"), max_length=1, null=True, blank=True)
    doviz_kodu = models.CharField(_("Döviz Kodu"), max_length=3, null=True, blank=True)
    doviz_boleni = models.CharField(_("Döviz Böleni"), max_length=1, null=True, blank=True)
    ozel_talimat_gostergesi = models.CharField(_("Özel Talimat Göstergesi"), max_length=2, null=True, blank=True)
    acilis_tarihi = models.CharField(_("Açılış Tarihi"), max_length=8, null=True, blank=True)
    basvuru_referans_numarasi = models.CharField(_("Başvuru Referans Numarası"), max_length=20, null=True, blank=True)
    kredi_turu = models.CharField(_("Kredi Türü"), max_length=25, choices=KrediTuru.choices, blank=True, null=True)
    faiz_orani_gostergesi = models.CharField(_("Faiz Oranı Göstergesi"), max_length=25, choices=FaizOraniGostergesi.choices, blank=True, null=True)
    kredi_kullanim_amaci = models.CharField(_("Kredi Kullanım Amacı"), max_length=25, choices=KrediKullanimAmaci.choices, blank=True, null=True)
    
    teminat_gostergesi = models.CharField(_("Teminat Göstergesi"), max_length=25, choices=TeminatGostergesi.choices, blank=True, null=True)
    kredi_tutari = models.CharField(_("Kredi Tutarı"), max_length=9, null=True, blank=True)
    depozito_tutari = models.CharField(_("Depozito Tutarı"), max_length=9, null=True, blank=True)
    sozlesme_suresi = models.CharField(_("Sözleşme Süresi"), max_length=3, null=True, blank=True)
    odeme_sikligi = models.CharField(_("Ödeme Sıklığı"), max_length=25, choices=OdemeSikligi.choices, blank=True, null=True)
    taksit_tutari = models.CharField(_("Taksit Tutarı"), max_length=9, null=True, blank=True)
    son_taksit_tutari = models.CharField(_("Son Taksit Tutarı"), max_length=9, null=True, blank=True)
    taksit_sayisi = models.CharField(_("Taksit Sayısı"), max_length=3, null=True, blank=True)
    odeme_sekli = models.CharField(_("Ödeme Şekli"), max_length=25, choices=OdemeSekli.choices, blank=True, null=True)
    kredi_limiti = models.CharField(_("Kredi Limiti"), max_length=9, null=True, blank=True)
    hesap_odeme_durumu = models.CharField(_("Hesap Ödeme Durumu"), max_length=25, choices=HesapOdemeDurumu.choices, blank=True, null=True)
    
    toplam_borc_bakiyesi = models.CharField(_("Toplam Borç Bakiyesi"), max_length=9, null=True, blank=True)
    kredi_bakiyesi_gostergesi = models.CharField(_("Kredi Bakiyesi Göstergesi"), max_length=25, choices=KrediBakiyesiGostergesi.choices, blank=True, null=True)
    borc_faizi_bakiyesi = models.CharField(_("Borç Faizi Bakiyesi"), max_length=9, null=True, blank=True)
    gecikmedeki_bakiye = models.CharField(_("Gecikmedeki Bakiye"), max_length=9, null=True, blank=True)
    vadesinde_yapilmayan_odeme = models.CharField(_("Vadesinde Yapılmayan Ödeme"), max_length=2, null=True, blank=True)
    son_odeme_tutari = models.CharField(_("Son Ödeme Tutarı"), max_length=9, null=True, blank=True)
    son_odeme_tarihi = models.CharField(_("Son Ödeme Tarihi"), max_length=8, null=True, blank=True)
    kapanis_tarihi = models.CharField(_("Kapanış Tarihi"), max_length=8, null=True, blank=True)

    kanuni_takip_tarihi = models.CharField(_("Kanuni Takip Tarihi"), max_length=8, null=True, blank=True)
    tahsil_edilme_tarihi = models.CharField(_("Tahsil Edilme Tarihi"), max_length=8, null=True, blank=True)

    kapanma_nedeni = models.CharField(_("Kapanma Nedeni"), max_length=25, choices=KapanmaNedeni.choices, blank=True, null=True)
    hesabin_ozel_durumu = models.CharField(_("Hesabın Özel Durumu"), max_length=25, choices=HesabinOzelDurumu.choices, blank=True, null=True)   

    yeni_hesap_numarasi = models.CharField(_("Yeni Hesap Numarası"), max_length=20, null=True, blank=True)

    kalan_taksit_bakiyesi = models.CharField(_("Kalan Taksit Bakiyesi"), max_length=9, null=True, blank=True)
    taksit_tarihi_gostergesi = models.CharField(_("Taksit Tarihi Göstergesi"), max_length=25, choices=TaksitTarihiGostergesi.choices, blank=True, null=True)
    yeniden_yapilandirma_gostergesi = models.CharField(_("Yeniden Yapılandırma Göstergesi"), max_length=25, choices=YenidenYapilandirmaGostergesi.choices, blank=True, null=True)
    yeniden_yapilandirma_tarihi = models.CharField(_("Yeniden Yapılandırma Tarihi"), max_length=8, null=True, blank=True)
    tedbir_karari_gostergesi = models.CharField(_("Tedbir Kararı Göstergesi"), max_length=25, choices=TedbirKarariGostergesi.choices, blank=True, null=True)
    kayittan_dusulen_tutar = models.CharField(_("Kayıttan Düşülen Tutar"), max_length=9, null=True, blank=True)
    nakit_cekim_tutari = models.CharField(_("Nakit Çekim Tutarı"), max_length=9, null=True, blank=True)
    gecikme_gun_sayisi = models.CharField(_("Gecikme Gün Sayısı"), max_length=2, null=True, blank=True)
    ekstre_odeme_orani = models.CharField(_("Ekstre Ödeme Oranı"), max_length=3, null=True, blank=True)




    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.uuid)
    
def krs_report_document_upload_path(instance, filename):
    return f"docs/{instance.company.uuid}/krs/krs_reports/documents/{filename}"

class KrsReportDocument(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="krs_report_documents")

    label = models.CharField(_("Label"), max_length=250, null=True, blank=True)
    file = models.FileField(_("File"), upload_to=krs_report_document_upload_path, null=True, blank=True, help_text=_("Please upload a file."))

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("KRS Rapor Dosyası")
        verbose_name_plural = _("KRS Rapor Dosyaları")

    def __str__(self):
        return str(f"{self.label}")