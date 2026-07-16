from django.contrib import admin

from .models import *


@admin.register(KapamaHareketi)
class KapamaHareketiAdmin(admin.ModelAdmin):
    list_display = (
        "contract_header_id", "tarih", "fatura_tutar", "odeme_tutar",
        "kapatilan_fatura_tutar", "temerrut_tutar", "bugune_kadar_temerrut", "sentetik",
    )
    list_filter = ("company", "sentetik")
    search_fields = ("contract_header_id",)
    date_hierarchy = "tarih"


@admin.register(KapamaDetay)
class KapamaDetayAdmin(admin.ModelAdmin):
    list_display = ("contract_header_id", "odeme_tarihi", "fatura_tarihi", "kapatilan_tutar")
    list_filter = ("company",)
    search_fields = ("contract_header_id",)
    date_hierarchy = "odeme_tarihi"


@admin.register(KrsTemerrutHavuz)
class KrsTemerrutHavuzAdmin(admin.ModelAdmin):
    list_display = (
        "contract_header_id", "rapor_tarihi", "en_eski_acik_fatura_gecikme_gun",
        "toplam_acik_bakiye", "toplam_bugune_kadar_temerrut", "risk_grubu",
    )
    list_filter = ("company", "risk_grubu", "rapor_tarihi")
    search_fields = ("contract_header_id",)
    date_hierarchy = "rapor_tarihi"

@admin.register(KrsReport)
class KrsReportAdmin(admin.ModelAdmin):
    list_display = ["company","uuid","contract","created_date"]
    list_display_links = ["uuid"]
    search_fields = ["company__name","contract__code","contract__contract_id"]
    list_filter = []
    inlines = []
    ordering = ["-created_date"]
    autocomplete_fields = ["company","contract"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def contract(self,obj):
        return obj.contract.code if obj.contract else ""
    
    class Meta:
        model = KrsReport

@admin.register(KrsReportDocument)
class KrsReportDocumentAdmin(admin.ModelAdmin):
    list_display = ["company","label","created_date"]
    list_display_links = ["label"]
    search_fields = ["company__name","label"]
    list_filter = []
    inlines = []
    ordering = ["-created_date"]
    autocomplete_fields = ["company"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    class Meta:
        model = KrsReportDocument