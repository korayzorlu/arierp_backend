from django.contrib import admin

from .models import AgentTask

@admin.register(AgentTask)
class AgentTaskAdmin(admin.ModelAdmin):

    list_display = ["company","user","agent_name","status","created_date"]
    list_display_links = ["user"]
    search_fields = ["company__name","user__name","agent_name","status"]
    list_filter = []
    inlines = []
    ordering = ["user"]
    autocomplete_fields = ["company","user"]

    def company(self,obj):
        return obj.company.name if obj.company else ""
    
    def user(self,obj):
        return obj.user.name if obj.user else ""
    
    class Meta:
        model = AgentTask