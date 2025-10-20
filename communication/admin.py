from django.contrib import admin
from django import forms

from .models import SMS

# Register your models here.

@admin.register(SMS)
class SMSAdmin(admin.ModelAdmin):
    list_display = ["company","category","partner","phone_number","packet_id","message_id","send_date","delivery_date","status"]
    list_display_links = ["phone_number"]
    search_fields = ["company__name","category","partner__name","phone_number","packet_id","message_id","send_date","delivery_date","status"]
    list_filter = []
    inlines = []
    ordering = ["-delivery_date"]
    autocomplete_fields = ["partner"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def partner(self,obj):
        return obj.contract.partner.name if obj.contract.partner else ""
    
    class Meta:
        model = SMS