from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt

from .views import *

app_name = 'agent'

urlpatterns = [
    path('run_agent/', RunAgentView.as_view(), name="run_agent"),
    path('agent_template/', AgentTemplateView.as_view(), name="agent_template"),
    path('get_agent_task/', csrf_exempt(GetAgentTaskView.as_view()), name="get_agent_task"),
    path('update_agent_task/', csrf_exempt(UpdateAgentTaskView.as_view()), name="update_agent_task"),

    path('', include("agent.api.urls")),
]