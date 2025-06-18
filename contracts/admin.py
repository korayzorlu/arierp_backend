from django.contrib import admin
from django import forms

from .models import Contract

# Register your models here.

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ["company","code","partner","kof_tan_sozlesmeye_aktarim_tarihi","lop_open_date"]
    list_display_links = ["code"]
    search_fields = ["company__name","code","partner__name","kof_tan_sozlesmeye_aktarim_tarihi","lop_open_date"]
    list_filter = []
    inlines = []
    ordering = ["kof_tan_sozlesmeye_aktarim_tarihi"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def partner(self,obj):
        return obj.partner.name if obj.partner else ""
    
    class Meta:
        model = Contract