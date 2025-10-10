from django.contrib import admin
from django import forms

from .models import Lease,Installment,BankActivity,BankActivityLease

# Register your models here.

@admin.register(Lease)
class LeaseAdmin(admin.ModelAdmin):
    list_display = ["company","partner","lease_id","code","project","activation_date","lease_status","lease_status_update_date"]
    list_display_links = ["code"]
    search_fields = ["company__name","lease_id","code","contract__partner__name","activation_date"]
    list_filter = []
    inlines = []
    ordering = ["activation_date"]
    autocomplete_fields = ["contract"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def partner(self,obj):
        return obj.contract.partner.name if obj.contract.partner else ""
    
    def project(self,obj):
        return obj.contract.project if obj.contract else ""
    
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

@admin.register(BankActivity)
class BankActivityAdmin(admin.ModelAdmin):
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
        model = BankActivity

@admin.register(BankActivityLease)
class BankActivityLeaseAdmin(admin.ModelAdmin):
    list_display = ["company","bank_activity","lease"]
    list_display_links = ["bank_activity"]
    search_fields = ["company__name","bank_activity__uuid","lease__code"]
    list_filter = []
    inlines = []
    ordering = ["created_date"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def bank_activity(self,obj):
        return obj.bank_activity.uuid if obj.bank_activity else ""
    
    def lease(self,obj):
        return obj.lease.code if obj.lease else ""
    
    class Meta:
        model = BankActivityLease