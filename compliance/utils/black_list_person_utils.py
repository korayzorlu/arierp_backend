from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value
from django.conf import settings
from django.http import JsonResponse

def is_valid_black_list_person_data(data):
    if not data.get('name'):
        return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    return True, None