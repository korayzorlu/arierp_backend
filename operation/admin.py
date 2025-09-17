from django.contrib import admin
from django import forms

from .models import *

# Register your models here.

@admin.register(PartnerAdvanceActivity)
class PartnerAdvanceActivityAdmin(admin.ModelAdmin):
    list_display = ["company","bank","bank_account_no","process_date","process_type","amount","currency","receipt_no","description","tc_vkn_no","cross_bank_account_no","created_date"]
    list_display_links = ["amount"]
    search_fields = ["company__name","bank","bank_account_no","process_date","process_type","amount","currency__code","receipt_no","description","tc_vkn_no","cross_bank_account_no"]
    list_filter = []
    inlines = []
    ordering = ["-updated_date"]
    autocomplete_fields = ["currency"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def currency(self,obj):
        return obj.currency.code if obj.currency else ""
    
    class Meta:
        model = PartnerAdvanceActivity

@admin.register(PartnerAdvanceActivityLease)
class PartnerAdvanceActivityLeaseAdmin(admin.ModelAdmin):
    list_display = ["company","partner_advance_activity","lease"]
    list_display_links = ["partner_advance_activity"]
    search_fields = ["company__name","partner_advance_activity__uuid","lease__code"]
    list_filter = []
    inlines = []
    ordering = ["created_date"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def partner_advance_activity(self,obj):
        return obj.partner_advance_activity.uuid if obj.partner_advance_activity else ""
    
    def lease(self,obj):
        return obj.lease.code if obj.lease else ""
    
    class Meta:
        model = PartnerAdvanceActivityLease