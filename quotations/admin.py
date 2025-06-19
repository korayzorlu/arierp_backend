from django.contrib import admin
from django import forms

from .models import QuickQuotation,Quotation

# Register your models here.

@admin.register(QuickQuotation)
class QuickQuotationAdmin(admin.ModelAdmin):
    list_display = ["company","code","quotation_no","partner"]
    list_display_links = ["code"]
    search_fields = ["company__name","code","partner__name","quotation_no"]
    list_filter = []
    inlines = []
    ordering = ["start_date"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def partner(self,obj):
        return obj.partner.name if obj.partner else ""
    
    class Meta:
        model = QuickQuotation

@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ["company","code","quick_quotation","partner"]
    list_display_links = ["code"]
    search_fields = ["company__name","code","quick_quotation__code","partner__name"]
    list_filter = []
    inlines = []
    ordering = ["request_date"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def partner(self,obj):
        return obj.partner.name if obj.partner else ""
    
    def quick_quotation(self,obj):
        return obj.quick_quotation.code if obj.quick_quotation else ""
    
    class Meta:
        model = Quotation