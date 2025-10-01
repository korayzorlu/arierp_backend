from django.http import JsonResponse

from quotations.models import *

def is_valid_quick_quotation_data(data):
    if not data.get('code') or not data.get('partner'):
        return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    return True, None

def is_valid_quotation_data(data):
    if not data.get('code') or not data.get('partner'):
        return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    return True, None