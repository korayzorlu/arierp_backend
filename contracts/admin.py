from django.contrib import admin
from django import forms

from .models import Contract,ContractPayment,WarningNotice,ComprehensiveWarningNotice,TerminationWarningNotice

# Register your models here.

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ["company","created_date_leaseflex","contract_id","code","partner","project","project_obj","vendor","kof_tan_sozlesmeye_aktarim_tarihi","lop_open_date","status"]
    list_display_links = ["code"]
    search_fields = ["company__name","contract_id","code","partner__name","project","project_obj__name","vendor__name","kof_tan_sozlesmeye_aktarim_tarihi","lop_open_date","status__name"]
    list_filter = []
    inlines = []
    ordering = ["kof_tan_sozlesmeye_aktarim_tarihi"]
    autocomplete_fields = ["partner","quotation_obj","vendor"]
    
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

@admin.register(ContractPayment)
class ContractPaymentAdmin(admin.ModelAdmin):
    list_display = ["company","trn_id","group_name","account_code","account_name","date","due_date","debit_amount","credit_amount","currency","local_debit_amount","local_credit_amount"]
    list_display_links = ["trn_id"]
    search_fields = ["company__name","trn_id","group_name","account_code","account_name","date","due_date","debit_amount","credit_amount","currency__code","local_debit_amount","local_credit_amount"]
    list_filter = []
    inlines = []
    ordering = ["-date"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def currency(self,obj):
        return obj.currency.code if obj.currency else ""
    
    class Meta:
        model = ContractPayment

@admin.register(WarningNotice)
class WarningNoticeAdmin(admin.ModelAdmin):
    list_display = ["company","contract","state","official_cancellation_date","process_start_date","service_date"]
    list_display_links = ["contract"]
    search_fields = ["company__name","contract__code","state","official_cancellation_date","process_start_date","service_date"]
    list_filter = []
    inlines = []
    ordering = ["-official_cancellation_date"]
    autocomplete_fields = ["contract"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def contract(self,obj):
        return obj.contract.code if obj.contract else ""
    
    class Meta:
        model = WarningNotice

@admin.register(ComprehensiveWarningNotice)
class ComprehensiveWarningNoticeAdmin(admin.ModelAdmin):
    list_display = ["company","contract","state","official_cancellation_date","process_start_date","service_date"]
    list_display_links = ["contract"]
    search_fields = ["company__name","contract__code","state","official_cancellation_date","process_start_date","service_date"]
    list_filter = []
    inlines = []
    ordering = ["-official_cancellation_date"]
    autocomplete_fields = ["contract"]

    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def contract(self,obj):
        return obj.contract.code if obj.contract else ""
    
    class Meta:
        model = ComprehensiveWarningNotice

@admin.register(TerminationWarningNotice)
class TerminationWarningNoticeAdmin(admin.ModelAdmin):
    list_display = ["company","contract"]
    list_display_links = ["contract"]
    search_fields = ["company__name","contract__code",]
    list_filter = []
    inlines = []
    ordering = ["-id"]
    autocomplete_fields = ["contract"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def contract(self,obj):
        return obj.contract.code if obj.contract else ""
    
    class Meta:
        model = TerminationWarningNotice