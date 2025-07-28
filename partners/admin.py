from django.contrib import admin
from django import forms

from .models import Partner,Sector

# Register your models here.

@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ["company","code","name","main_sector_code","match_code","kkbmb_sector_code"]
    list_display_links = ["name"]
    search_fields = ["company__name","code","name","main_sector_code","match_code","kkbmb_sector_code"]
    list_filter = []
    inlines = []
    ordering = ["name"]
    
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    class Meta:
        model = Sector

class PartnerAdminForm(forms.ModelForm):
    TYPES_CHOICES = (
        ('customer', ('Customer')),
        ('supplier', ('Supplier')),
        ('shareholder', ('Shareholder')),
        ('special', ('Special')),
        ('barter', ('Barter')),
        ('virman', ('Virman')),
    )

    types = forms.MultipleChoiceField(
        choices=TYPES_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Partner
        fields = '__all__'

@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    form = PartnerAdminForm
    
    list_display = ["company","types","customer_code","crm_code","name","formal_name","tc_vkn_no","country","city"]
    list_display_links = ["name"]
    search_fields = ["company__name","customer_code","crm_code","name","formal_name","tc_vkn_no","country__name","city__name"]
    list_filter = []
    inlines = []
    ordering = ["name"]
    autocomplete_fields = ["country","billing_country","phone_country","city","billing_city","sector"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    def country(self,obj):
        return obj.country.name if obj.country else ""
    def city(self,obj):
        return obj.city.name if obj.city else ""
    
    def display_types(self, obj):
        return ", ".join(obj.types or [])
    display_types.short_description = "Types"
    
    class Meta:
        model = Partner
