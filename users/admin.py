from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Register your models here.
from .models import *

# class UserAdmin(admin.ModelAdmin):
#     model = User
#     list_display = ['email', 'first_name', 'last_name', 'is_active']

#admin.site.register(User, UserAdmin)
admin.site.register(Profile)

@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ["username","email","first_name", "last_name"]
    list_display_links = ["username"]
    search_fields = ["username","email","first_name","last_name"]
    list_filter = []
    inlines = []
    ordering = ["email"]

    fieldsets = UserAdmin.fieldsets + (
        ("More details", {"fields": ["is_email_verified","phone_country","phone_number","verify_sid"]}),
    )
    
    class Meta:
        model = User