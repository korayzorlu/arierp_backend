from django.contrib import admin
from django import forms

from .models import PurchasePayment

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