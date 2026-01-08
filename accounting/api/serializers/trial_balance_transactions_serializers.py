from rest_framework import serializers

from accounting.models import *
from users.models import User

class TrialBalanceTransactionListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    transaction_id = serializers.CharField()
    trial_balance = serializers.SerializerMethodField()
    trial_balance_uuid = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    account_name = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    main_account_code = serializers.SerializerMethodField()
    ledger_period = serializers.CharField()
    transaction_text = serializers.CharField()
    amount_type = serializers.CharField()
    local_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    transaction_date = serializers.DateTimeField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''

    def get_trial_balance(self, obj):
        return obj.trial_balance.account_code if obj.trial_balance else ''
    
    def get_trial_balance_uuid(self, obj):
        return obj.trial_balance.uuid if obj.trial_balance else ''
    
    def get_user(self, obj):
        user = User.objects.filter(leaseflex_id=obj.user_id).first()
        return user.get_full_name() if user else ''
    
    def get_account_name(self, obj):
        return obj.trial_balance.account_name if obj.trial_balance else ''
    
    def get_currency(self, obj):
        return obj.trial_balance.currency.code if obj.trial_balance and obj.trial_balance.currency else ''
    
    def get_main_account_code(self, obj):
        return obj.trial_balance.main_account_code if obj.trial_balance else ''


