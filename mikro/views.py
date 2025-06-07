from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from celery.result import AsyncResult

import json

from .models import *
from .tasks import *

# Create your views here.

class SetVpnView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        #task = setVpn.delay("srger")
        return JsonResponse({'taskId': task.id})
    
class GetVpnStatusView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        id = data.get('id')
        print(id)
        task = AsyncResult(id)
        print(task)
        return JsonResponse({"taskId": id, "status": task.status})