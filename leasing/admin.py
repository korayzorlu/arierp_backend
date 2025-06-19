from django.contrib import admin
from django import forms

from .models import Lease

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