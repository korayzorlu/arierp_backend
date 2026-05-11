from django.contrib import admin
from django import forms

from .models import Partner,Sector,PartnerNote, SgkJob,PartnerFinancialProfile

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

@admin.register(SgkJob)
class SgkJobAdmin(admin.ModelAdmin):
    list_display = ["company","sgk_job_id","sgk_job_code","description","is_pep"]
    list_display_links = ["sgk_job_code"]
    search_fields = ["company__name","sgk_job_id","sgk_job_code","description"]
    list_filter = []
    inlines = []
    ordering = ["sgk_job_code"]
    
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    class Meta:
        model = SgkJob

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
    
    list_display = ["company","types","customer_code","crm_code","name","formal_name","tc_vkn_no","country","city","phone_number"]
    list_display_links = ["name"]
    search_fields = ["company__name","customer_code","crm_code","name","formal_name","tc_vkn_no","country__name","city__name","phone_number"]
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

@admin.register(PartnerFinancialProfile)
class PartnerFinancialProfileAdmin(admin.ModelAdmin):

    list_display = ["company","partner","income_types","other_income","created_date","updated_date"]
    list_display_links = ["partner"]
    search_fields = ["company__name","partner__name","income_types","other_income"]
    list_filter = []
    inlines = []
    ordering = ["partner"]
    autocomplete_fields = ["company","partner"]

    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def partner(self,obj):
        return obj.partner.name if obj.partner else ""
    
    class Meta:
        model = PartnerFinancialProfile
@admin.register(PartnerNote)
class PartnerNoteAdmin(admin.ModelAdmin):

    list_display = ["company","partner","title","text","user","created_date","updated_date"]
    list_display_links = ["title"]
    search_fields = ["company__name","partner__name","user__first_name","user__last_name","title","text"]
    list_filter = []
    inlines = []
    ordering = ["title"]
    autocomplete_fields = ["company","user","partner"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    def user(self,obj):
        return obj.user.get_full_name() if obj.user else ""
    class Meta:
        model = PartnerNote