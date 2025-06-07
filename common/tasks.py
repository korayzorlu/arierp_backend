from celery import shared_task
from core.celery import app
from django.http import JsonResponse

import pandas as pd
import io

from .models import ImportProcess
from .utils.import_utils import BaseImporter
from users.models import User


@shared_task(bind=True)
def importData(self,df_json,user_id,app,model_name):
    importer = BaseImporter(user_id=user_id, app=app, model_name=model_name, task_id=self.request.id)
    importer.process_import(df_json)