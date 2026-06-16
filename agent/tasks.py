from celery import shared_task
from core.celery import app
from django.http import JsonResponse

from agent.utils.common_utils import AgentEngine
from common.utils.websocket_utils import send_alert,send_agent_status

@shared_task(bind=True)
def agentData(self,df_json,user_id,agent_name,lf_username, lf_password):
    agent_engine = AgentEngine(user_id=user_id, agent_name=agent_name, lf_username=lf_username, lf_password=lf_password)
    agent_engine.agent_task(df_json)

@shared_task
def reject_pending_agent_task(agent_task_id):
    from agent.models import AgentTask
    AgentTask.objects.filter(id=agent_task_id, status='pending').update(status='rejected')
    if AgentTask.objects.filter(id=agent_task_id, status='pending').exists():
        send_agent_status({"running": False}, room=f"private_{agent_task_id}")
        send_alert({"message": "Agent görevi reddedildi!", 'status': 'error'}, room=f"private_{agent_task_id}")