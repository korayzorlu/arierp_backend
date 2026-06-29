from django.contrib import admin
from django import forms

from .models import SMS,Email,EmailReceiver,SetrowEmail,Call
from common.utils.common_utils import duration_to_hhmmss

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

@admin.register(SetrowEmail)
class SetrowEmailAdmin(admin.ModelAdmin):
    list_display = ["company","sender","send_id","template","recipient","send_date","user","send_status"]
    list_display_links = ["send_id"]
    search_fields = ["company__name","send_date","template","user__name","recipient","sender","send_status"]
    list_filter = []
    inlines = []
    ordering = ["-created_date"]
    autocomplete_fields = ["company","user"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def user(self,obj):
        return obj.user.username if obj.user else ""
    
    def send_status(self,obj):
        return obj.get_send_status_display() if obj.send_status else ""
    
    class Meta:
        model = SetrowEmail

@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    list_display = ["company","partner","queue","agent","direction","phone_number","start_time","end_time","connected_length_method","disposition","verdict"]
    list_display_links = ["phone_number"]
    search_fields = ["company__name","partner__name","queue","agent","direction","phone_number","start_time","end_time","disposition","verdict"]
    list_filter = []
    inlines = []
    ordering = ["-start_time"]
    autocomplete_fields = ["company","partner"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def partner(self,obj):
        return obj.partner.name if obj.partner else ""
    
    def connected_length_method(self,obj):
        if obj.connected_length:
            return duration_to_hhmmss(obj.connected_length)
        return ""
    
    class Meta:
        model = Call