from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import JsonResponse, FileResponse, HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils.crypto import get_random_string
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.mail import EmailMessage, send_mail

from utils.mixins import CompanyOwnershipRequiredMixin,ActivityLogMixin

from common.utils.websocket_utils import send_alert,send_agent_status
from .utils.common_utils import AgentEngine
from .models import AgentTask

import json
import os
import base64

# Create your views here.

class RunAgentView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.POST.get('data', '{}'))
        file = request.FILES.get('file')
        
        agent_engine = AgentEngine(
            user_id=request.user.id,
            agent_name=data.get("agentName"),
            file=file,
            lf_username=data.get("lf_username"),
            lf_password=data.get("lf_password")
        )

        if agent_engine.validate_authorization() != 200:
            return JsonResponse(agent_engine.validate_authorization(), status=403)

        if agent_engine.validate_file() != 200:
            return JsonResponse(agent_engine.validate_file(), status=400)

        send_agent_status({"running": True},room=f"private_{request.user.uuid}")
        send_alert({"message":"Agent işlemi başlatıldı!",'status':'success'},room=f"private_{request.user.uuid}")

        df_json = agent_engine.read_file()
        if isinstance(df_json, dict):
            return JsonResponse(df_json, status=400)
            
        agent_engine.start_agent(df_json)     

        return HttpResponse(status=200)
    
class AgentTemplateView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "files", "agent", "ihtar-cekilecekler.xlsx")

        if not os.path.exists(file_path):
            return JsonResponse({'message': 'Dosya bulunamadı!','status':'error'}, status=404)

        return FileResponse(open(file_path, 'rb'))
    
class GetAgentTaskView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        #return JsonResponse({"task": None}, status=400)

        agent_token = request.headers.get("X-Agent-Token")
        if agent_token != settings.AGENT_SECRET_TOKEN:
            return HttpResponse(status=403)

        task = AgentTask.objects.filter(
            status = "pending",
            user__username = data.get("username")
        ).first()

        if task is None:
            return JsonResponse({"task": None}, status=400)

        agent_path = os.path.join(settings.BASE_DIR, "agent", "utils", "agents", f"{task.agent_name}.py")
        try:
            with open(agent_path, "r", encoding="utf-8") as f:
                agent_code = f.read()
        except FileNotFoundError:
            task.status = "rejected"
            task.save()
            return JsonResponse({"task": None}, status=400)

        with task.file.open("rb") as f:
            excel_b64 = base64.b64encode(f.read()).decode()

        task_data = {
            "task_id": task.uuid,
            "agent_code": agent_code,
            "excel_b64": excel_b64,
            "username": task.lf_username,
            "password": task.lf_password
        }

        return JsonResponse(task_data, status=200)
    
class UpdateAgentTaskView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)

        task = AgentTask.objects.filter(
            uuid = data.get("task_id")
        ).first()

        if task is None:
            return JsonResponse({'message': 'Task bulunamadı!','status':'error'}, status=404)
        task.status = data.get("status", task.status)
        task.log = data.get("log", task.log)
        task.save()

        if task.status == "completed" or task.status == "rejected":
            send_agent_status({"running": False},room=f"private_{task.user.uuid}")
            send_alert({"message": f"{'Agent işlemi başarılı şekilde tamamlandı' if task.status == 'completed' else 'Agent işleminde hata oluştu'}!",'status':'success' if task.status == "completed" else 'error'},room=f"private_{task.user.uuid}")

        return JsonResponse({'message': 'Task kaydedildi!','status':'success'}, status=200)