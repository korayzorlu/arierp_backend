from celery import shared_task
from core.celery import app
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

import pandas as pd
import io

from common.models import ImportProcess
from users.models import User

def sendAlert(message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'public_room',
        {
            "type": "send_alert",
            "message": message,
        }
    )

@shared_task(bind=True)
def importPartners(self,df_json,user_id):
    #process = ImportProcess.objects.filter(model_name="Partner",user__id=user_id,task_id=self.request.id)
    user = User.objects.filter(id = user_id).first()
    process = ImportProcess.objects.create(
            user = user,
            model_name = "Partner",
            task_id = self.request.id,
            status = "in_progress"
        )
    process.save()

    # if not process:
    #     return {"error": "Process not found!"}
    
    df = pd.read_json(io.StringIO(df_json), orient='records')

    for index,row in df.iterrows():
        if pd.isnull(row["name"]) or row["name"] == "":
            process.status = "rejected"
            process.save()
            process.delete()
            return
        
        print(row["name"])

    process.status = "completed"
    process.save()
        
