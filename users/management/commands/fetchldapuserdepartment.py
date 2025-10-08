from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from users.tasks import fetch_ldap_user_department

class Command(BaseCommand):
    help = 'Exports parts to JSON file'
    
    def get_or_none(classmodel, **kwargs):
        try:
            return classmodel.objects.get(**kwargs)
        except classmodel.DoesNotExist:
            return None

    def add_arguments(self, parser):
        parser.add_argument('-c', type=str, help='Company to associate with operation')
        parser.add_argument('-u', type=str, help='User ID to fetch department information')

    def handle(self, *args, **options):
        company = options.get('c')
        user = options.get('u')

        print("processing...")
        
        fetch_ldap_user_department.delay(company,user)
        
        print("done!")