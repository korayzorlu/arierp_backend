from celery import shared_task
from core.celery import app
from django.http import JsonResponse

from agent.utils.common_utils import AgentEngine

@shared_task(bind=True)
def agentData(self,df_json,user_id,agent_name,lf_username, lf_password):
    agent_engine = AgentEngine(user_id=user_id, agent_name=agent_name, lf_username=lf_username, lf_password=lf_password)
    agent_engine.agent_task(df_json)