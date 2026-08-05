from django.contrib import admin
from django import forms

from .models import *

# Register your models here.

@admin.register(RealEstateAgent)
class RealEstateAgentAdmin(admin.ModelAdmin):
    list_display = ["company","name","phone_number_1","phone_number_2","url","created_date"]
    list_display_links = ["name"]
    search_fields = ["company__name","name","phone_number_1","phone_number_2","url"]
    list_filter = []
    inlines = []
    ordering = ["-created_date"]
    autocomplete_fields = []
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    class Meta:
        model = RealEstateAgent

@admin.register(WhatsappMessage)
class WhatsappMessageAdmin(admin.ModelAdmin):
    list_display = ["company","real_estate_agent","created_date"]
    list_display_links = ["real_estate_agent"]
    search_fields = ["company__name","real_estate_agent__name"]
    list_filter = []
    inlines = []
    ordering = ["-created_date"]
    autocomplete_fields = []
    
    def company(self,obj):
        return obj.company.name if obj.company else ""

    def real_estate_agent(self,obj):
        return obj.real_estate_agent.name if obj.real_estate_agent else ""
    
    class Meta:
        model = WhatsappMessage
