from django.contrib import admin
from django import forms

from .models import *

# Register your models here.

@admin.register(TradeAccount)
class TradeAccountAdmin(admin.ModelAdmin):
    list_display = ["company","account_id","partner","name","crm_id","crm_type"]
    list_display_links = ["name"]
    search_fields = ["company__name","account_id","partner__name","name","crm_id","crm_type"]
    list_filter = []
    inlines = []
    ordering = ["account_id"]
    autocomplete_fields = ["partner"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def partner(self,obj):
        return obj.partner.name if obj.partner else ""
    
    class Meta:
        model = TradeAccount

@admin.register(TradeTransaction)
class TradeTransactionAdmin(admin.ModelAdmin):
    list_display = ["company","trade_transaction_id","partner","lease","posting_group_name","description","currency","amount"]
    list_display_links = ["trade_transaction_id"]
    search_fields = ["company__name","trade_transaction_id","partner__name","lease__code","posting_group_name","description","currency__name"]
    list_filter = []
    inlines = []
    ordering = ["trade_transaction_id"]
    autocomplete_fields = ["partner","lease","currency"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def partner(self,obj):
        return obj.partner.name if obj.partner else ""
    
    def lease(self,obj):
        return obj.lease.code if obj.lease else ""
    
    def currency(self,obj):
        return obj.currency.code if obj.currency else ""
    
    class Meta:
        model = TradeTransaction

