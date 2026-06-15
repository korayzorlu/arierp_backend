from django.urls import path, include

from .views import *

app_name = 'agent'

urlpatterns = [
    path('run_agent/', RunAgentView.as_view(), name="run_agent"),
    path('agent_template/', AgentTemplateView.as_view(), name="agent_template"),

    path('', include("agent.api.urls")),
]