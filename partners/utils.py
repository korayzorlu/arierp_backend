from django.http import JsonResponse

def is_valid_sector_data(data):
    if not data.get('code') or not data.get('name') or not data.get('mainSectorCode') or not data.get('matchCode') or not data.get('kkbmbSectorCode'):
        return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    return True, None

def is_valid_partner_data(data):
    if not data.get('name') or not data.get('formalName'):
        return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    if not data.get('customer') and not data.get('supplier') and not data.get('shareholder') and not data.get('special'):
        return False, JsonResponse({'message': 'You must select at least one option, either Customer or Supplier or Shareholder!','status':'error'}, status=400)
    return True, None

def get_partner_types(data):
    types = []
    if data.get('customer'):
        types.append("customer")
    if data.get('supplier'):
        types.append("supplier")
    if data.get('shareholder'):
        types.append("shareholder")
    if data.get('special'):
        types.append("special")
    return types

