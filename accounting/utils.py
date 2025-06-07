from django.http import JsonResponse

def is_valid_account_data(data):
    if data.get('type') == 'receivable' or data.get('type') == 'payable' or data.get('type') == 'shareholder':
        if not data.get('partner'):
            return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    if not data.get('currency'):
        return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    
    return True, None

def is_valid_invoice_data(data):
    if not data.get('partner') or not data.get('currency') or not data.get('invoice_no') or not data.get('amount'):
        return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    
    return True, None

def is_valid_payment_data(data):
    if not data.get('partner') or not data.get('currency') or not data.get('amount'):
        return False, JsonResponse({'message': 'Fill required fields.','status':'error'}, status=400)
    
    return True, None

# model save processes
def get_or_create_account(company,currency,type,partner=None):
    from .models import Account,AccountType
    filters = {'currency': currency, 'type__code': type}
    if partner:
        filters['partner'] = partner
    account = Account.objects.filter(**filters).first()

    if not account:
        account_type = AccountType.objects.filter(code=type).first()
        account = Account.objects.create(
            company=company,
            partner=partner,
            currency=currency,
            type=account_type
        )
        account.save()
    return account

def create_transaction(company, type, account, amount, ref_uuid, description=""):
    from .models import Transaction
    transaction = Transaction.objects.create(
        company=company,
        type=type,
        account=account,
        amount=amount,
        ref_uuid=ref_uuid,
        description=description
    )
    transaction.save()

    return transaction