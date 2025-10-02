from django.http import JsonResponse

def is_valid_contract_data(data):
    if not data.get('code') or not data.get('partner'):
        return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    return True, None