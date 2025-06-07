from django.contrib import admin

from .models import *

# Register your models here.

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user","title", "message","is_read","created_date"]
    list_display_links = ["title"]
    search_fields = ["user__email","title","message","is_read","created_date"]
    list_filter = []
    inlines = []
    ordering = ["-id"]
    
    def user(self,obj):
        return obj.user.email if obj.user else ""
    
    class Meta:
        model = Notification