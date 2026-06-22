from django.contrib import admin

from . import models


@admin.register(models.KapamaHareketi)
class KapamaHareketiAdmin(admin.ModelAdmin):
    list_display = (
        "contract_header_id", "tarih", "fatura_tutar", "odeme_tutar",
        "kapatilan_fatura_tutar", "temerrut_tutar", "bugune_kadar_temerrut", "sentetik",
    )
    list_filter = ("company", "sentetik")
    search_fields = ("contract_header_id",)
    date_hierarchy = "tarih"


@admin.register(models.KapamaDetay)
class KapamaDetayAdmin(admin.ModelAdmin):
    list_display = ("contract_header_id", "odeme_tarihi", "fatura_tarihi", "kapatilan_tutar")
    list_filter = ("company",)
    search_fields = ("contract_header_id",)
    date_hierarchy = "odeme_tarihi"


@admin.register(models.KrsTemerrutHavuz)
class KrsTemerrutHavuzAdmin(admin.ModelAdmin):
    list_display = (
        "contract_header_id", "rapor_tarihi", "en_eski_acik_fatura_gecikme_gun",
        "toplam_acik_bakiye", "toplam_bugune_kadar_temerrut", "risk_grubu",
    )
    list_filter = ("company", "risk_grubu", "rapor_tarihi")
    search_fields = ("contract_header_id",)
    date_hierarchy = "rapor_tarihi"
