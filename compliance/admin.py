from django.contrib import admin
from django import forms

from .models import BlackListPerson,ThirdPerson

# Register your models here.

@admin.register(BlackListPerson)
class BlackListPersonAdmin(admin.ModelAdmin):
    list_display = ["company","name","tc_vkn_passport_no"]
    list_display_links = ["name"]
    search_fields = ["company__name","name","tc_vkn_passport_no"]
    list_filter = []
    inlines = []
    ordering = ["name"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    class Meta:
        model = BlackListPerson

@admin.register(ThirdPerson)
class ThirdPersonAdmin(admin.ModelAdmin):
    list_display = ["company","name","tc_vkn_no","status"]
    list_display_links = ["name"]
    search_fields = ["company__name","name","tc_vkn_no","status"]
    list_filter = []
    inlines = []
    ordering = ["name"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    class Meta:
        model = ThirdPerson