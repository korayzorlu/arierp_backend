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

# TODO: gerçek import yolunuza göre düzeltin, örn:
#   from common.models import Company
from common.models import Company  # noqa: F401


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
