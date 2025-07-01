from django.contrib import admin
from django import forms

from .models import *

# Register your models here.

@admin.register(LedgerAccount)
class LedgerAccountAdmin(admin.ModelAdmin):
    list_display = ["company","account_id","code","name","currency"]
    list_display_links = ["name"]
    search_fields = ["company__name","account_id","code","currency__code"]
    list_filter = []
    inlines = []
    ordering = ["account_id"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def currency(self,obj):
        return obj.currency.code if obj.currency else ""
    
    class Meta:
        model = LedgerAccount

