from django.contrib import admin
from django import forms

from .models import PurchasePayment

# Register your models here.

@admin.register(PurchasePayment)
class PurchasePaymentAdmin(admin.ModelAdmin):
    list_display = ["company"]
    list_display_links = []
    search_fields = []
    list_filter = []
    inlines = []
    ordering = ["id"]
    autocomplete_fields = ["company"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    class Meta:
        model = PurchasePayment