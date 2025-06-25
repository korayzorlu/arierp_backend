from django.contrib import admin
from django import forms

from .models import Lease,Installment

# Register your models here.

@admin.register(Lease)
class LeaseAdmin(admin.ModelAdmin):
    list_display = ["company","code","partner","activation_date"]
    list_display_links = ["code"]
    search_fields = ["company__name","code","contract__partner__name","activation_date"]
    list_filter = []
    inlines = []
    ordering = ["activation_date"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def partner(self,obj):
        return obj.contract.partner.name if obj.contract.partner else ""
    
    class Meta:
        model = Lease

@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    list_display = ["company","lease","amount","principal","payment_date","sequency"]
    list_display_links = ["lease"]
    search_fields = ["company__name","lease__code","payment_date"]
    list_filter = []
    inlines = []
    ordering = ["lease__code","sequency"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def lease(self,obj):
        return obj.lease.code if obj.lease else ""
    
    class Meta:
        model = Installment