from django.contrib import admin

from .models import *

# Register your models here.

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user","type", "duration", "startDate", "endDate"]
    list_display_links = ["user"]
    search_fields = ["user__email","type","duration", "startDate", "endDate"]
    list_filter = ["startDate"]
    inlines = []
    ordering = ["-pk"]
    
    def user(self,obj):
        return obj.user.email if obj.user else ""
    class Meta:
        model = Subscription

@admin.register(Authorization)
class AuthorizationAdmin(admin.ModelAdmin):
    list_display = ["user","department"]
    list_display_links = ["user"]
    search_fields = ["user__email","department"]
    list_filter = []
    inlines = []
    ordering = ["-pk"]
    
    def user(self,obj):
        return obj.user.email if obj.user else ""
    class Meta:
        model = Authorization