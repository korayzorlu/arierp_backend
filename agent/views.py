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

from common.utils.websocket_utils import send_alert
from .utils.common_utils import AgentEngine

import json
import os

# Create your views here.

class RunAgentView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.POST.get('data', '{}'))
        file = request.FILES.get('file')

        agent_engine = AgentEngine(user_id=request.user.id, agent_name=data.get("agentName"), file=file)

        if agent_engine.validate_file() != 200:
            return JsonResponse(agent_engine.validate_file(), status=400)

        if not request.user.is_authenticated:
            return JsonResponse({'message': 'Yetki hatası!.','status':'error'}, status=401)
        
        if request.user.authorization.department != 'kredi_risk_izleme':
            return JsonResponse({'message': 'Bu işlem için yetkiniz yok!','status':'error'}, status=403)
        
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