from django.contrib import admin
from django import forms

from .models import Partner

# Register your models here.

class PartnerAdminForm(forms.ModelForm):
    TYPES_CHOICES = [
        ('customer', 'Customer'),
        ('supplier', 'Supplier')
    ]

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
    
    list_display = ["company","types","name","formal_name","country","city"]
    list_display_links = ["name"]
    search_fields = ["company__name","name","formal_name","country__name","city__name"]
    list_filter = []
    inlines = []
    ordering = ["name"]
    
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
