from django.contrib import admin
from django import forms

from .models import Project

# Register your models here.

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["company","project_id","name","partner"]
    list_display_links = ["name"]
    search_fields = ["company__name","partner__name","project_id","name"]
    list_filter = []
    inlines = []
    ordering = ["id"]
    autocomplete_fields = ["partner","company"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def partner(self,obj):
        return obj.partner.name if obj.partner else ""
    
    class Meta:
        model = Project