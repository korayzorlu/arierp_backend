from django.contrib import admin

from .models import *

# Register your models here.

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ["name","formal_name","iso2","iso3","dial_code"]
    list_display_links = ["name"]
    search_fields = ["name","formal_name","iso2","iso3","dial_code"]
    list_filter = []
    inlines = []
    ordering = ["id"]
    
    class Meta:
        model = Country

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ["country","name"]
    list_display_links = ["name"]
    search_fields = ["country__name","name"]
    list_filter = []
    inlines = []
    ordering = ["id"]

    def user(self,obj):
        return obj.country.name if obj.country else ""
    
    class Meta:
        model = City

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ["countries_display","code","name","symbol","exchange_rate"]
    list_display_links = ["code"]
    search_fields = ["code","name","symbol","exchange_rate"]
    list_filter = []
    inlines = []
    ordering = ["id"]

    def countries_display(self, obj):
        countries = obj.countries.all()
        return ", ".join([country.name for country in countries]) if countries else "-"
    countries_display.short_description = "Countries"
    
    class Meta:
        model = Currency
        
@admin.register(ImportProcess)
class ImportProcessAdmin(admin.ModelAdmin):
    list_display = ["task_id","status","user","model_name","created_date"]
    list_display_links = ["task_id"]
    search_fields = ["task_id","status","user__email","model_name","created_date"]
    list_filter = []
    inlines = []
    ordering = ["-id"]

    def user(self,obj):
        return obj.user.email if obj.user else ""
    
    class Meta:
        model = ImportProcess