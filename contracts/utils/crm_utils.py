from datetime import datetime

from django.db.models import Q,Max,Sum,Count,Case,When,BooleanField,Value
from django.conf import settings
from django.http import JsonResponse
from django.utils.timezone import now,localtime
from decimal import Decimal, InvalidOperation

from companies.models import Company

def is_valid_contract_form_data(data):
    parameters = [
        'ApartmentTypeName',
        'AnuualRateMonth',
        'CashSalesTotalAmount',
        'CompanyId',
        'ContractHeaderCode',
        'CurrencyCode',
        'CurrentSaleTotalAmount',
        'CustomerName',
        'CustomerSignDate',
        'DownPaymentAmount',
        'Email',
        'FreePartUnitType',
        'FreeValidationPeriodText',
        'IslandNo',
        'Kep',
        'LeasingAmount',
        'Maturity',
        'MobilPhone', 
        'NumberOfPeopleStay',
        'OtherAddress',
        'OtherPhone',
        'ParcelNo',
        'PlannedDeliveryDate',
        'ProjectName',
        'TaxAndTCIdentity',
        'TaxRate',
        'TimeSharePeriodPartText',
        'ValidationKey',
        'WorkPhone',
        'YazismaAddress',
        
    ]

    unknown_keys = set(data.keys()) - set(parameters)

    #zorunlu parametrelerin kontrolü
    if unknown_keys:
        return False, JsonResponse({'message': f'Geçersiz parametre(ler): {", ".join(sorted(unknown_keys))}', 'status': 'error'}, status=400)
    
    if not data.get('CompanyId') or not Company.objects.filter(uuid=data.get('CompanyId')).exists():
        return False, JsonResponse({'message': 'Şirket bilgisi eksik veya geçersiz! (CompanyId)','status':'error'}, status=400)
    
    if not data.get('ValidationKey') or data.get('ValidationKey') != settings.CONTRACT_FORM_VALIDATION_KEY:
        return False, JsonResponse({'message': 'Doğrulama anahtarı geçersiz! (ValidationKey)','status':'error'}, status=400)
    
    if not data.get('ContractHeaderCode') or not isinstance(data.get('ContractHeaderCode'), str):
        return False, JsonResponse({'message': 'Sözleşme kodu eksik veya geçersiz! (ContractHeaderCode)','status':'error'}, status=400)
    
    if not data.get('CustomerName') or not isinstance(data.get('CustomerName'), str):
        return False, JsonResponse({'message': 'Müşteri ismi eksik veya geçersiz! (CustomerName)','status':'error'}, status=400)
    
    if not data.get('TaxAndTCIdentity') or not isinstance(data.get('TaxAndTCIdentity'), str):
        return False, JsonResponse({'message': 'Vergi numarası veya TC kimlik numarası eksik veya geçersiz! (TaxAndTCIdentity)','status':'error'}, status=400)
    
    if not data.get('YazismaAddress') or not isinstance(data.get('YazismaAddress'), str):
        return False, JsonResponse({'message': 'Yazışma adresi eksik veya geçersiz! (YazismaAddress)','status':'error'}, status=400)

    if not data.get('IslandNo') or not isinstance(data.get('IslandNo'), str):
        return False, JsonResponse({'message': 'Ada numarası eksik veya geçersiz! (IslandNo)','status':'error'}, status=400)
    
    if not data.get('ParcelNo') or not isinstance(data.get('ParcelNo'), str):
        return False, JsonResponse({'message': 'Parsel numarası eksik veya geçersiz! (ParcelNo)','status':'error'}, status=400)
    
    if not data.get('ProjectName') or not isinstance(data.get('ProjectName'), str):
        return False, JsonResponse({'message': 'Proje adı eksik veya geçersiz! (ProjectName)','status':'error'}, status=400)
    
    if not data.get('FreePartUnitType') or not isinstance(data.get('FreePartUnitType'), str):
        return False, JsonResponse({'message': 'Birim tipi eksik veya geçersiz! (FreePartUnitType)','status':'error'}, status=400)
    
    if not data.get('TimeSharePeriodPartText') or not isinstance(data.get('TimeSharePeriodPartText'), str):
        return False, JsonResponse({'message': 'Devre tatil dönemi eksik veya geçersiz! (TimeSharePeriodPartText)','status':'error'}, status=400)
    
    if not data.get('NumberOfPeopleStay') or not isinstance(data.get('NumberOfPeopleStay'), int):
        return False, JsonResponse({'message': 'Kalan kişi sayısı eksik veya geçersiz! (NumberOfPeopleStay)','status':'error'}, status=400)
    
    if not data.get('CustomerSignDate') or not isinstance(data.get('CustomerSignDate'), str):
        return False, JsonResponse({'message': 'Sözleşme/imza tarihi eksik veya geçersiz! (CustomerSignDate)','status':'error'}, status=400)
    
    if not data.get('TaxRate') or not isinstance(data.get('TaxRate'), int):
        return False, JsonResponse({'message': 'KDV oranı eksik veya geçersiz! (TaxRate)','status':'error'}, status=400)
    
    raw_amount = data.get('CurrentSaleTotalAmount')
    if not isinstance(raw_amount, str) or not raw_amount.strip():
        return False, JsonResponse({'message': 'Toplam sözleşme bedeli eksik veya geçersiz! (CurrentSaleTotalAmount)','status':'error'}, status=400)
    try:
        current_sale_total_amount = Decimal(raw_amount.strip())
    except InvalidOperation:
        return False, JsonResponse({'message': 'Toplam sözleşme bedeli eksik veya geçersiz! (CurrentSaleTotalAmount)','status':'error'}, status=400)
    
    if not data.get('CurrencyCode') or not isinstance(data.get('CurrencyCode'), str):
        return False, JsonResponse({'message': 'Para birimi eksik veya geçersiz! (CurrencyCode)','status':'error'}, status=400)
    
    #zorunlu olmayan parametrelerin kontrolü
    if data.get('WorkPhone') and not isinstance(data.get('WorkPhone'), str):
        return False, JsonResponse({'message': 'İş telefonu geçersiz! (WorkPhone)','status':'error'}, status=400)
    
    if data.get('OtherAddress ') and not isinstance(data.get('OtherAddress '), str):
        return False, JsonResponse({'message': 'Yurt dışı adres geçersiz! (OtherAddress )','status':'error'}, status=400)
    
    if data.get('MobilePhone ') and not isinstance(data.get('MobilePhone '), str):
        return False, JsonResponse({'message': 'Mobil tel geçersiz! (MobilePhone )','status':'error'}, status=400)
    
    if data.get('Email') and not isinstance(data.get('Email'), str):
        return False, JsonResponse({'message': 'E-posta geçersiz! (Email)','status':'error'}, status=400)
    
    if data.get('Kep') and not isinstance(data.get('Kep'), str):
        return False, JsonResponse({'message': 'Kep adresi geçersiz! (Kep)','status':'error'}, status=400)
    
    if data.get('ApartmentTypeName') and not isinstance(data.get('ApartmentTypeName'), str):
        return False, JsonResponse({'message': 'Bina tipi geçersiz! (ApartmentTypeName)','status':'error'}, status=400)
    
    if data.get('FreeValidationPeriodText ') and not isinstance(data.get('FreeValidationPeriodText '), str):
        return False, JsonResponse({'message': 'Dönem yazısı geçersiz! (FreeValidationPeriodText )','status':'error'}, status=400)
    
    planned_delivery_date = data.get('PlannedDeliveryDate')
    if planned_delivery_date:
        if not isinstance(planned_delivery_date, str):
            return False, JsonResponse({'message': 'Planlanan teslim tarihi geçersiz! (PlannedDeliveryDate)','status':'error'}, status=400)
        try:
            datetime.strptime(planned_delivery_date, '%Y-%m-%d')
        except ValueError:
            return False, JsonResponse({'message': 'Planlanan teslim tarihi geçersiz! (PlannedDeliveryDate formatı YYYY-MM-DD olmalıdır)','status':'error'}, status=400)
    
    if data.get('Maturity') and not isinstance(data.get('Maturity'), int):
        return False, JsonResponse({'message': 'Ödeme süresi geçersiz! (Maturity)','status':'error'}, status=400)
    
    if data.get('CurrentSaleTotalAmount'):
        raw_amount = data.get('CurrentSaleTotalAmount')
        if not isinstance(raw_amount, str) or not raw_amount.strip():
            return False, JsonResponse({'message': 'Baz maliyet eksik veya geçersiz! (CurrentSaleTotalAmount)','status':'error'}, status=400)
        try:
            current_sale_total_amount = Decimal(raw_amount.strip())
        except InvalidOperation:
            return False, JsonResponse({'message': 'Baz maliyet eksik veya geçersiz! (CurrentSaleTotalAmount)','status':'error'}, status=400)
    
    if data.get('LeasingAmount'):
        raw_amount = data.get('LeasingAmount')
        if not isinstance(raw_amount, str) or not raw_amount.strip():
            return False, JsonResponse({'message': 'Finansal kiralama geliri eksik veya geçersiz! (LeasingAmount)','status':'error'}, status=400)
        try:
            leasing_amount = Decimal(raw_amount.strip())
        except InvalidOperation:
            return False, JsonResponse({'message': 'Finansal kiralama geliri eksik veya geçersiz! (LeasingAmount)','status':'error'}, status=400)
    
    if data.get('DownPaymentAmount'):
        raw_amount = data.get('DownPaymentAmount')
        if not isinstance(raw_amount, str) or not raw_amount.strip():
            return False, JsonResponse({'message': 'Peşinat eksik veya geçersiz! (DownPaymentAmount)','status':'error'}, status=400)
        try:
            down_payment_amount = Decimal(raw_amount.strip())
        except InvalidOperation:
            return False, JsonResponse({'message': 'Peşinat eksik veya geçersiz! (DownPaymentAmount)','status':'error'}, status=400)
    
    return True, None