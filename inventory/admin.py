from django.contrib import admin
from django import forms

from .models import *

# Register your models here.

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = [
        "company",
        "stock_code_id",
        "stock_code",
        "stock_name",
        "item_group_id",
        "item_group_code",
        "item_group_name",
        "item_group_type",
        "fixed_asset_group",
        "explanation",
        "item_group_type_id",
        "bddk_code",
    ]
    list_display_links = ["stock_name"]
    search_fields = [
        "company__name",
        "stock_code_id",
        "stock_code",
        "stock_name",
        "item_group_id",
        "item_group_code",
        "item_group_name",
        "item_group_type",
        "fixed_asset_group",
        "explanation",
        "item_group_type_id",
        "bddk_code",
    ]
    list_filter = []
    inlines = []
    ordering = ["stock_code_id"]
    autocomplete_fields = ["company"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    class Meta:
        model = Item