from django.contrib import admin
from django import forms

from .models import BankaTahsilati,BankaTahsilatiOdoo

# Register your models here.

@admin.register(BankaTahsilati)
class BankaTahsilatiAdmin(admin.ModelAdmin):
    list_display = ["company","gonderen_unvani","tc_vkn_no","aciklama","tutar"]
    list_display_links = ["gonderen_unvani"]
    search_fields = ["company__name","gonderen_unvani","tc_vkn_no","aciklama","tutar"]
    list_filter = []
    inlines = []
    ordering = ["gonderen_unvani"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    class Meta:
        model = BankaTahsilati

@admin.register(BankaTahsilatiOdoo)
class BankaTahsilatiOdooAdmin(admin.ModelAdmin):
    list_display = ["company","gonderen_unvani","tc_vkn_no","aciklama","tutar"]
    list_display_links = ["gonderen_unvani"]
    search_fields = ["company__name","gonderen_unvani","tc_vkn_no","aciklama","tutar"]
    list_filter = []
    inlines = []
    ordering = ["gonderen_unvani"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    class Meta:
        model = BankaTahsilatiOdoo