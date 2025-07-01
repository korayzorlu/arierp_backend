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

