from django.contrib import admin
from django import forms

from .models import Project,Parcel,RealEstate,TitleDeed

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

@admin.register(Parcel)
class ParcelAdmin(admin.ModelAdmin):
    list_display = ["company","project","parcel_id","no"]
    list_display_links = ["no"]
    search_fields = ["company__name","project__name","parcel_id","no"]
    list_filter = []
    inlines = []
    ordering = ["id"]
    autocomplete_fields = ["project","company"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def project(self,obj):
        return obj.project.name if obj.project else ""
    
    class Meta:
        model = Parcel

@admin.register(RealEstate)
class RealEstateAdmin(admin.ModelAdmin):
    list_display = ["company","project","real_estate_id","parcel","block","unit"]
    list_display_links = ["block"]
    search_fields = ["company__name","project__name","real_estate_id","parcel","block","unit"]
    list_filter = []
    inlines = []
    ordering = ["id"]
    autocomplete_fields = ["project","company"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def project(self,obj):
        return obj.project.name if obj.project else ""
    
    class Meta:
        model = RealEstate

@admin.register(TitleDeed)
class TitleDeedAdmin(admin.ModelAdmin):
    list_display = ["company","tasinmaz_no","nitelik","il","ilce","mahalle","ada","parsel"]
    list_display_links = ["tasinmaz_no"]
    search_fields = ["company__name","tasinmaz_no","nitelik","il","ilce","mahalle","ada","parsel"]
    list_filter = []
    inlines = []
    ordering = ["id"]
    autocomplete_fields = ["company"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    class Meta:
        model = TitleDeed