from django.apps import apps
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import BooleanField,QuerySet, Q
from django.db.models.functions import Lower,Upper
from django.utils.crypto import get_random_string
from django.utils.timezone import localtime, make_aware, is_naive


import pandas as pd
import io
import os
from decimal import Decimal
from openai import OpenAI
from datetime import datetime
import time
import ast
import pickle

from users.models import User
from agent.models import *
from .registry import get_agent_function
from common.utils.websocket_utils import send_alert

class AgentEngine():
    allowed_extensions = ["xls", "xlsx"]
    max_file_size = 5 * 1024 * 1024
    max_rows = 10_000

    def __init__(self, user_id, agent_name, file=None, task_id=None):
        self.file = file
        self.user = User.objects.filter(id = int(user_id)).first()
        self.agent_name = agent_name
        self.task_id = task_id
        self.status = "pending"
        self.process = None
        self.df = None

    def validate_file(self):
        if not self.file:
            return {"message": "Dosya bulunamadı!", "status":"error"}
        
        file_size = self.file.size
        if file_size > self.max_file_size:
            return {"message": f"Dosya çok büyük! Maksimum {self.max_file_size // (1024 * 1024)}MB izin verilmektedir.", "status":"error"}

        file_name, file_extension = os.path.splitext(self.file.name)
        file_extension = file_extension.lower().lstrip('.')

        if file_extension not in self.allowed_extensions:   
            return {"message": "Desteklenmeyen dosya türü! Sadece xls ve xlsx dosyaları yükleyebilirsiniz.", "status":"error"}

        return 200

    def read_file(self):
        try:
            excel_file = pd.ExcelFile(self.file)
            first_sheet_name = excel_file.sheet_names[0]
            
            file_data = pd.read_excel(self.file, first_sheet_name)
            df = pd.DataFrame(file_data)
            self.df = df

            return df.to_json(orient='records')
        except Exception as e:
            return {"message": f"Dosya okuma hatası: {str(e)}", "status":"error"}

    def start_agent(self, df_json):
        from agent.tasks import agentData
        agentData.delay(df_json, self.user.id, self.agent_name)

    def agent_task(self, df_json):
        self.task = AgentTask.objects.create(
            company = self.user.user_companies.filter(is_active=True).first().company,
            user = self.user,
            status = self.status,
            task_id = self.task_id
        )
        self.task.save()
        
        agent_function = get_agent_function(self.agent_name.lower())
        if not agent_function:
            self.task.status = "rejected"
            self.task.save()
            send_alert({"message":"Bir hata oluştu!",'status':'error'},room=f"private_{self.user.uuid}")
            #return {"message": "Bir hata oluştu!", "status":"error"}

        try:
            agent_function(self, df_json)
            self.task.status = "completed"
            self.task.save()
        except Exception as e:
            self.task.status = "rejected"
            self.task.save()
            return {"message": f"Bir hata oluştu!", "status":"error"}

        

            
