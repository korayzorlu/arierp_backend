from django.contrib import admin
from django import forms

from .models import Project

# Register your models here.

# @admin.register(Project)
# class ProjectAdmin(admin.ModelAdmin):
#     list_display = ["company","project_id","name"]
#     list_display_links = ["code"]
#     search_fields = ["company__name","lease_id","code","contract__partner__name","activation_date"]
#     list_filter = []
#     inlines = []
#     ordering = ["activation_date"]
#     autocomplete_fields = ["contract"]
    
#     def company(self,obj):
#         return obj.company.name if obj.company else ""
    
#     def partner(self,obj):
#         return obj.contract.partner.name if obj.contract.partner else ""
    
#     class Meta:
#         model = Project