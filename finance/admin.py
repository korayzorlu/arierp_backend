from django.contrib import admin
from django import forms

from .models import FinmaksBankAccount,FinmaksTransaction,FinmaksBankAccountDailyRecord,VPosTransaction,VPosIletisim

# Register your models here.

@admin.register(FinmaksBankAccount)
class FinmaksBankAccountAdmin(admin.ModelAdmin):
    list_display = ["company","bank_name","iban","account_no","finmaks_account_type","currency","currency_type","status"]
    list_display_links = ["bank_name"]
    search_fields = ["company__name","bank_name","iban","account_no","finmaks_account_type","currency__code","currency_type","status"]
    list_filter = []
    inlines = []
    ordering = ["bank_name"]
    autocomplete_fields = ["currency"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def currency(self,obj):
        return obj.currency.code if obj.currency else ""
    
    class Meta:
        model = FinmaksBankAccount

@admin.register(FinmaksBankAccountDailyRecord)
class FinmaksBankAccountDailyRecordAdmin(admin.ModelAdmin):
    list_display = ["company","finmaks_bank_account","date","balance","available_balance"]
    list_display_links = ["finmaks_bank_account"]
    search_fields = ["company__name","finmaks_bank_account__bank_name","date","balance","available_balance"]
    list_filter = []
    inlines = []
    ordering = ["-date"]
    autocomplete_fields = ["finmaks_bank_account"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def finmaks_bank_account(self,obj):
        return obj.finmaks_bank_account.bank_name if obj.finmaks_bank_account else ""
    
    class Meta:
        model = FinmaksBankAccountDailyRecord

@admin.register(FinmaksTransaction)
class FinmaksTransactionAdmin(admin.ModelAdmin):
    list_display = ["company","bank_account","transaction_id","explanation_field","transaction_date"]
    list_display_links = ["transaction_id"]
    search_fields = ["company__name","bank_account__bank_name","transaction_id","explanation_field","transaction_date"]
    list_filter = []
    inlines = []
    ordering = ["-transaction_date"]
    autocomplete_fields = ["bank_account"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def bank_account(self,obj):
        return obj.bank_account.bank_name if obj.bank_account else ""
    
    class Meta:
        model = FinmaksTransaction

@admin.register(VPosTransaction)
class VPosTransactionAdmin(admin.ModelAdmin):
    list_display = ["company","paid_amount","currency","created_date"]
    list_display_links = ["paid_amount"]
    search_fields = ["company__name","currency__code","created_date"]
    list_filter = []
    inlines = []
    ordering = ["-created_date"]
    autocomplete_fields = ["currency"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def currency(self,obj):
        return obj.currency.code if obj.currency else ""
    
    class Meta:
        model = VPosTransaction

@admin.register(VPosIletisim)
class VPosIletisimAdmin(admin.ModelAdmin):
    list_display = ["vpos_transaction","iletisim_turu","iletisim_degeri"]
    list_display_links = ["vpos_transaction"]
    search_fields = ["vpos_transaction__company__name","vpos_transaction__paid_amount","vpos_transaction__currency__code","vpos_transaction__created_date","iletisim_turu","iletisim_degeri"]
    list_filter = []
    inlines = []
    ordering = ["-vpos_transaction__created_date"]
    autocomplete_fields = ["vpos_transaction"]
    
    def company(self,obj):
        return obj.vpos_transaction.company.name if obj.vpos_transaction and obj.vpos_transaction.company else ""
    
    class Meta:
        model = VPosIletisim