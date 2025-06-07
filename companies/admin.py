from django.contrib import admin

from .models import *

# Register your models here.

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["user","name", "formal_name"]
    list_display_links = ["name"]
    search_fields = ["user__email","name","formal_name"]
    list_filter = []
    inlines = []
    ordering = ["-id"]
    
    def user(self,obj):
        return obj.user.email if obj.user else ""
    
    class Meta:
        model = Company

@admin.register(UserCompany)
class UserCompanyAdmin(admin.ModelAdmin):
    list_display = ["user","company", "is_active", "is_admin"]
    list_display_links = ["company"]
    search_fields = ["user__email","company__name","is_active","is_admin"]
    list_filter = []
    inlines = []
    ordering = ["-id"]
    
    def user(self,obj):
        return obj.user.email if obj.user else ""
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    class Meta:
        model = UserCompany

@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ["token","sender","recipient", "company", "status"]
    list_display_links = ["token"]
    search_fields = ["sender__email","recipient__email","company__name","status"]
    list_filter = []
    inlines = []
    ordering = ["-id"]
    
    def sender(self,obj):
        return obj.sender.email if obj.sender else ""
    
    def recipient(self,obj):
        return obj.recipient.email if obj.recipient else ""
    
    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    class Meta:
        model = Invitation
