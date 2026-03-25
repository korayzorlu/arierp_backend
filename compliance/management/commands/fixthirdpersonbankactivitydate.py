from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from contracts.models import *
from compliance.models import *
from compliance.tasks import fix_third_person_bank_activity_date
from leasing.models import BankActivity

from datetime import datetime, date

class Command(BaseCommand):
    help = 'Exports items to JSON file'
    
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

        fix_third_person_bank_activity_date.delay(company)

        print("done!")