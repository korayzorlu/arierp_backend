from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import traceback

from users.tasks import fetch_ldap_all_users
from users.utils import fetch_ldap_departments_info

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
        
        #fetch_ldap_all_users.delay(company)
        try:
            data = fetch_ldap_departments_info()

            for index,obj in enumerate(data):
                print(obj)
                print("--------")
        except Exception as e:
            print(e)
            traceback.print_exc()
        
        print("done!")