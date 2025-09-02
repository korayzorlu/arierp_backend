from django.contrib import admin
from django import forms

from .models import FinmaksBankAccount

# Register your models here.

@admin.register(FinmaksBankAccount)
class FinmaksBankAccountAdmin(admin.ModelAdmin):
    list_display = ["company","bank_name","iban","account_no","currency"]
    list_display_links = ["bank_name"]
    search_fields = ["company__name","bank_name","iban","account_no","currency__code"]
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