def match_bank_activity_from_iban(params):
    from leasing.models import BankActivity
    objs = BankActivity.objects.select_related().filter(cross_bank_account_no = params.cross_bank_account_no).exclude(pk=params.exclude_pk)
    return objs