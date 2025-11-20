from django.contrib import admin
from django import forms

from .models import BlackListPerson,ThirdPerson,ThirdPersonDocument

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

@admin.register(ThirdPersonDocument)
class ThirdPersonDocumentAdmin(admin.ModelAdmin):
    list_display = ["company","third_person","label"]
    list_display_links = ["label"]
    search_fields = ["company__name","third_person__name","label"]
    list_filter = []
    inlines = []
    ordering = ["label"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def third_person(self,obj):
        return obj.third_person.name if obj.third_person else ""
    
    class Meta:
        model = ThirdPersonDocument