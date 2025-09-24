from django.contrib import admin
from django import forms

from .models import FinmaksBankAccount,FinmaksTransaction

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

@admin.register(FinmaksTransaction)
class FinmaksTransactionAdmin(admin.ModelAdmin):
    list_display = ["company","bank_account","transaction_id","transaction_date"]
    list_display_links = ["transaction_id"]
    search_fields = ["company__name","bank_account__bank_name","transaction_id","transaction_date"]
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