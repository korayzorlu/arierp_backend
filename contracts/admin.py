from django.contrib import admin
from django import forms

from .models import Contract

# Register your models here.

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ["company","contract_id","code","partner","project","project_obj","vendor","kof_tan_sozlesmeye_aktarim_tarihi","lop_open_date","status"]
    list_display_links = ["code"]
    search_fields = ["company__name","contract_id","code","partner__name","project","project_obj__name","vendor__name","kof_tan_sozlesmeye_aktarim_tarihi","lop_open_date","status__name"]
    list_filter = []
    inlines = []
    ordering = ["kof_tan_sozlesmeye_aktarim_tarihi"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def partner(self,obj):
        return obj.partner.name if obj.partner else ""
    
    def project_obj(self,obj):
        return obj.project_obj.name if obj.project_obj else ""
    
    def vendor(self,obj):
        return obj.vendor.name if obj.vendor else ""
    
    def status(self,obj):
        return obj.status.name if obj.status else ""
    
    class Meta:
        model = Contract