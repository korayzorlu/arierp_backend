from django.contrib import admin
from django import forms

from .models import SMS,Email,EmailReceiver

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

@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ["company","send_date","user","recievers","sender",]
    list_display_links = ["send_date"]
    search_fields = ["company__name","send_date","user__name","receivers__email","sender"]
    list_filter = []
    inlines = []
    ordering = ["-created_date"]
    autocomplete_fields = ["company","user"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def user(self,obj):
        return obj.user.name if obj.user else ""
    
    def recievers(self,obj):
        return ", ".join([receiver.email for receiver in obj.receivers.all()])
    
    class Meta:
        model = Email

@admin.register(EmailReceiver)
class EmailReceiverAdmin(admin.ModelAdmin):
    list_display = ["company","email","created_date"]
    list_display_links = ["email"]
    search_fields = ["company__name","email","created_date"]
    list_filter = []
    inlines = []
    ordering = ["-created_date"]
    autocomplete_fields = ["company"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    class Meta:
        model = EmailReceiver