from django.contrib import admin
from django import forms

from .models import *

# Register your models here.

@admin.register(AccountCategory)
class AccountCategoryAdmin(admin.ModelAdmin):
    list_display = ["code","name"]
    list_display_links = ["name"]
    search_fields = ["code","name"]
    list_filter = []
    inlines = []
    ordering = ["code"]
    
    class Meta:
        model = AccountCategory

@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ["category","code","name"]
    list_display_links = ["name"]
    search_fields = ["code","name","category__name"]
    list_filter = []
    inlines = []
    ordering = ["category__name","code"]

    def category(self,obj):
        return obj.category.name if obj.category else ""
    
    class Meta:
        model = AccountType

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["company","partner","type","currency","balance"]
    list_display_links = ["partner"]
    search_fields = ["company__name","partner__name","type","currency__code","balance"]
    list_filter = []
    inlines = []
    ordering = ["company__name","partner__name"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    def partner(self,obj):
        return obj.partner.name if obj.partner else ""
    def currency(self,obj):
        return obj.currency.code if obj.currency else ""
    
    class Meta:
        model = Account

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["company__name","account","date","type","amount","currency"]
    list_display_links = ["account"]
    search_fields = ["account__partner__name","date","type","amount","account__currency__code"]
    list_filter = []
    inlines = []
    ordering = ["company__name","account__partner__name"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    def account(self,obj):
        return obj.acount.partner.name if obj.account else ""
    def currency(self,obj):
        return obj.account.currency.code if obj.account else ""
    
    class Meta:
        model = Transaction

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["company","partner","type","currency","amount"]
    list_display_links = ["partner"]
    search_fields = ["company__name","partner__name","type","currency__code","amount"]
    list_filter = []
    inlines = []
    ordering = ["company__name","partner__name"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    def partner(self,obj):
        return obj.partner.name if obj.partner else ""
    def currency(self,obj):
        return obj.currency.code if obj.currency else ""
    
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()
    
    class Meta:
        model = Invoice

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["company","partner","type","currency","amount"]
    list_display_links = ["partner"]
    search_fields = ["company__name","partner__name","type","currency__code","amount"]
    list_filter = []
    inlines = []
    ordering = ["company__name","partner__name"]
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    def partner(self,obj):
        return obj.partner.name if obj.partner else ""
    def currency(self,obj):
        return obj.currency.code if obj.currency else ""
    
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()
    
    class Meta:
        model = Payment