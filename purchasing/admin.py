from django.contrib import admin
from django import forms

from .models import PurchasePayment,PurchaseDocument,PurchaseDocumentItem

# Register your models here.

@admin.register(PurchasePayment)
class PurchasePaymentAdmin(admin.ModelAdmin):
    list_display = ["company", "lease"]
    list_display_links = []
    search_fields = ["lease__code", "company__name","lease__id"]
    list_filter = []
    inlines = []
    ordering = ["id"]
    autocomplete_fields = ["company", "lease"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def lease(self,obj):
        return obj.lease.code if obj.lease else ""
    
    class Meta:
        model = PurchasePayment

@admin.register(PurchaseDocument)
class PurchaseDocumentAdmin(admin.ModelAdmin):
    list_display = ["company", "document_id", "code", "document_number", "document_date", "lease", "partner", "vendor", "amount", "vat_amount", "total_amount", "currency", "exchange_rate", "document_status"]
    list_display_links = ["document_id"]
    search_fields = ["document_id", "code", "document_number", "lease__code", "partner__name", "vendor__name", "company__name"]
    list_filter = []
    inlines = []
    ordering = ["id"]
    autocomplete_fields = ["company", "lease", "partner", "vendor", "currency"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def lease(self,obj):
        return obj.lease.code if obj.lease else ""
    
    def partner(self,obj):
        return obj.partner.name if obj.partner else ""
    
    def vendor(self,obj):
        return obj.vendor.name if obj.vendor else ""
    
    def currency(self,obj):
        return obj.currency.code if obj.currency else ""
    
    class Meta:
        model = PurchaseDocument

@admin.register(PurchaseDocumentItem)
class PurchaseDocumentItemAdmin(admin.ModelAdmin):
    list_display = ["company", "purchase_document", "document_line_id", "quantity", "unit_amount", "amount","vat_amount","total_amount"]
    list_display_links = ["document_line_id"]
    search_fields = ["document_line_id", "purchase_document__document_id", "purchase_document__code", "purchase_document__document_number","company__name"]
    list_filter = []
    inlines = []
    ordering = ["id"]
    autocomplete_fields = ["purchase_document", "company"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def purchase_document(self,obj):
        return obj.purchase_document.document_id if obj.purchase_document else ""
    
    class Meta:
        model = PurchaseDocumentItem