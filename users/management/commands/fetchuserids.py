from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import pyodbc
import os

from users.tasks import fetch_ldap_data
from users.models import User

class Command(BaseCommand):
    help = 'Exports parts to JSON file'
    
    def get_or_none(classmodel, **kwargs):
        try:
            return classmodel.objects.get(**kwargs)
        except classmodel.DoesNotExist:
            return None

    def add_arguments(self, parser):
        parser.add_argument('-c', type=str, help='Company to associate with operation')

    def handle(self, *args, **options):
        company = options.get('c')

        print("processing...")
        
        conn = pyodbc.connect(settings.ARI_CONNECTION_STRING)

        SQL_PATH = os.path.join(settings.BASE_DIR, "users","sql","kullanicilar.sql")
        with open(SQL_PATH, "r", encoding="utf-8") as file:
            SQL_QUERY = file.read()

        cursor = conn.cursor()
        cursor.execute(SQL_QUERY)
        cursor.fast_executemany = True

        records = cursor.fetchmany(10000)

        for index,data in enumerate(records):
            user = User.objects.select_related().filter(username=str(data.UserName)).first()
            if user:
                user.leaseflex_id = str(data.UserId)
                user.save()
        print("done!")