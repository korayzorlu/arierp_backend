from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value
from django.conf import settings
from django.http import JsonResponse
from django.utils.timezone import now,localtime

from companies.models import Company

def is_valid_contract_form_data(data):
    parameters = [
        'CompanyId',
        'ContractHeaderCode',
        'CustomerName',
        'Email',
        'KepAddress',
        'MobilPhone', 
        'OtherAddress',
        'OtherPhone',
        'TaxAndTCIdentity',
        'ValidationKey',
        'WorkPhone',
        'YazismaAddress'
    ]

    unknown_keys = set(data.keys()) - set(parameters)
    if unknown_keys:
        return False, JsonResponse({'message': f'Geçersiz parametre(ler): {", ".join(sorted(unknown_keys))}', 'status': 'error'}, status=400)
    
    if not data.get('CompanyId') or not Company.objects.filter(uuid=data.get('CompanyId')).exists():
        return False, JsonResponse({'message': 'Şirket bilgisi eksik veya geçersiz! (CompanyId)','status':'error'}, status=400)
    
    if not data.get('ValidationKey') or data.get('ValidationKey') != settings.CONTRACT_FORM_VALIDATION_KEY:
        return False, JsonResponse({'message': 'Doğrulama anahtarı geçersiz! (ValidationKey)','status':'error'}, status=400)
    
    if not data.get('CustomerName') or not isinstance(data.get('CustomerName'), str):
        return False, JsonResponse({'message': 'Müşteri ismi eksik! (CustomerName)','status':'error'}, status=400)
    
    if not data.get('TaxAndTCIdentity') or not isinstance(data.get('TaxAndTCIdentity'), str):
        return False, JsonResponse({'message': 'Vergi numarası veya TC kimlik numarası eksik! (TaxAndTCIdentity)','status':'error'}, status=400)
    
    return True, None