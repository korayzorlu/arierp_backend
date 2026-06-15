from celery import shared_task
from core.celery import app
from django.http import JsonResponse

from agent.utils.common_utils import AgentEngine

@shared_task(bind=True)
def agentData(self,df_json,user_id,agent_name):
    agent_engine = AgentEngine(user_id=user_id, agent_name=agent_name, file=None, task_id=self.request.id)
    agent_engine.agent_task(df_json)