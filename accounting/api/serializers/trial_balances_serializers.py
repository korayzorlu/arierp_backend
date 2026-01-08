from rest_framework import serializers

from accounting.models import *
from leasing.models import Lease

class TrialBalanceListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    partner = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    account_id = serializers.CharField()
    main_account_code = serializers.CharField()
    # main_account_code_list = serializers.SerializerMethodField()
    account_code = serializers.CharField()
    account_code_trim = serializers.CharField()
    account_name = serializers.CharField()
    balance_account_type = serializers.CharField()
    balance_debit = serializers.DecimalField(max_digits=14,decimal_places=2)
    balance_credit = serializers.DecimalField(max_digits=14,decimal_places=2)
    total_debit = serializers.DecimalField(max_digits=14,decimal_places=2)
    total_credit = serializers.DecimalField(max_digits=14,decimal_places=2)
    total_tl = serializers.SerializerMethodField()
    balance_debit_alternate = serializers.DecimalField(max_digits=14,decimal_places=2)
    balance_credit_alternate = serializers.DecimalField(max_digits=14,decimal_places=2)
    total_debit_alternate = serializers.DecimalField(max_digits=14,decimal_places=2)
    total_credit_alternate = serializers.DecimalField(max_digits=14,decimal_places=2)
    total_currency = serializers.SerializerMethodField()
    contract = serializers.SerializerMethodField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_partner(self, obj):
        return obj.partner.name if obj.partner else ''
    
    def get_currency(self, obj):
        return obj.currency.code if obj.currency else ''

    def get_total_tl(self, obj):
        return obj.balance_debit - obj.balance_credit

    def get_total_currency(self, obj):
        return obj.balance_debit_alternate - obj.balance_credit_alternate
    
    # def get_main_account_code_list(self, obj):
    #     main_account_codes = TrialBalance.objects.values_list('main_account_code', flat=True).distinct()

    #     return main_account_codes
    
    def get_contract(self, obj):
        return obj.contract.code if obj.contract else ''
    
class TrialBalanceContractListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    code = serializers.CharField()
    contract_id = serializers.CharField()
    partner = serializers.SerializerMethodField()
    partner_tc = serializers.SerializerMethodField()
    kof = serializers.CharField()
    committe = serializers.CharField()
    credit_type = serializers.CharField()
    customer_representative = serializers.CharField()
    supplier = serializers.CharField()
    mkk_tesciline_gonderilecek_mi = serializers.BooleanField()
    kof_tan_sozlesmeye_aktarim_tarihi = serializers.DateTimeField()
    lop_open_date = serializers.DateTimeField()
    created_date_leaseflex = serializers.DateTimeField()
    trial_balances = serializers.SerializerMethodField()
    lease_status = serializers.SerializerMethodField()
    transfer_count = serializers.SerializerMethodField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
        
    def get_partner(self, obj):
        return obj.partner.name if obj.partner else ""
    
    def get_partner_tc(self, obj):
        return obj.partner.tc_vkn_no if obj.partner else ""
    
    def get_lease_status(self, obj):
        lease = obj.contract_leases.filter(is_last_project = True).first()
        return lease.get_lease_status_display() if lease else ""
    
    def get_transfer_count(self, obj):
        last_lease = obj.contract_leases.filter(is_last_project = True).first()
        return last_lease.transfer_count if last_lease else 0
    
    def get_trial_balances(self, obj):
        last_lease = obj.contract_leases.filter(is_last_project = True).first()
        leases = Lease.objects.select_related("contract").filter(main_lease_id=last_lease.main_lease_id,is_last_project = True).order_by('-lease_id')

        trial_balance_dict = {"trial_balances": [],"transfer_count": len(leases) - 1 if len(leases) > 0 else 0, "max_overdue_days": "" }

        for lease in leases:
            #lease = obj.contract_leases.filter(is_last_project = True).first()
            trial_balances = lease.contract.contract_trial_balances.select_related("currency","contract","partner").all()
            for trial_balance in trial_balances:
                trial_balance_dict["trial_balances"].append({
                    "id" : trial_balance.uuid,
                    "partner" : trial_balance.partner.name if trial_balance.partner else "",
                    "currency" : trial_balance.currency.code if trial_balance.currency else "",
                    "account_id" : trial_balance.account_id,
                    "main_account_code" : trial_balance.main_account_code,
                    "account_code" : trial_balance.account_code,
                    "account_code_trim" : trial_balance.account_code_trim,
                    "account_name" : trial_balance.account_name,
                    "balance_account_type" : trial_balance.balance_account_type,
                    "balance_debit" : trial_balance.balance_debit,
                    "balance_credit" : trial_balance.balance_credit,
                    "total_debit" : trial_balance.total_debit,
                    "total_credit" : trial_balance.total_credit,
                    "total_tl" : trial_balance.balance_debit - trial_balance.balance_credit,
                    "balance_debit_alternate" : trial_balance.balance_debit_alternate,
                    "balance_credit_alternate" : trial_balance.balance_credit_alternate,
                    "total_debit_alternate" : trial_balance.total_debit_alternate,
                    "total_credit_alternate" : trial_balance.total_credit_alternate,
                    "total_currency" : trial_balance.balance_debit_alternate - trial_balance.balance_credit_alternate,
                    "contract" : trial_balance.contract.code if trial_balance.contract else "",
                    "lease_status" : lease.get_lease_status_display() if lease else "",
                })
        #return sorted(lease_dict, key=lambda x: x["leases"]["overdue_days"], reverse=True)

        return trial_balance_dict

class UnderReviewListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    

class UnderReviewListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    code = serializers.CharField()
    contract_id = serializers.CharField()
    partner = serializers.SerializerMethodField()
    partner_tc = serializers.SerializerMethodField()
    kof = serializers.CharField()
    quotation = serializers.SerializerMethodField()
    committe = serializers.CharField()
    credit_type = serializers.CharField()
    customer_representative = serializers.CharField()
    supplier = serializers.CharField()
    vendor = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    mkk_tesciline_gonderilecek_mi = serializers.BooleanField()
    kof_tan_sozlesmeye_aktarim_tarihi = serializers.DateTimeField()
    lop_open_date = serializers.DateTimeField()
    created_date_leaseflex = serializers.DateTimeField()
    is_commercial = serializers.SerializerMethodField()
    trial_balances = serializers.SerializerMethodField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_quotation(self, obj):
        return obj.quotation_obj.code if obj.quotation_obj else ""
        
    def get_partner(self, obj):
        return obj.partner.name if obj.partner else ""
    
    def get_is_commercial(self, obj):
        return obj.partner.is_commercial if obj.partner else False
    
    def get_partner_tc(self, obj):
        return obj.partner.tc_vkn_no if obj.partner else ""
    
    def get_vendor(self, obj):
        return obj.vendor.name if obj.vendor else ""
    
    def get_status(self, obj):
        return obj.status.name if obj.status else ""
    
    def get_trial_balances(self, obj):
        request = self.context.get('request')
        filter_params = request.GET if request else {}
        
        trial_balances = obj.contract_trial_balances.select_related("currency").all()

        trial_balance_dict = {"trial_balances": [],"total_overdue_amount": "", "max_overdue_days": "" }
        if trial_balances:
            for trial_balance in trial_balances:
                trial_balance_dict["trial_balances"].append({
                    "id" : trial_balance.uuid,
                    "partner" : trial_balance.partner.name,
                    "currency" : trial_balance.currency.code if trial_balance.currency else "",
                    "account_id" : trial_balance.account_id,
                    "main_account_code" : trial_balance.main_account_code,
                    "account_code" : trial_balance.account_code,
                    "account_code_trim" : trial_balance.account_code_trim,
                    "account_name" : trial_balance.account_name,
                    "balance_account_type" : trial_balance.balance_account_type,
                    "balance_debit" : trial_balance.balance_debit,
                    "balance_credit" : trial_balance.balance_credit,
                    "total_debit" : trial_balance.total_debit,
                    "total_credit" : trial_balance.total_credit,
                    "total_tl" : trial_balance.balance_debit - trial_balance.balance_credit,
                    "balance_debit_alternate" : trial_balance.balance_debit_alternate,
                    "balance_credit_alternate" : trial_balance.balance_credit_alternate,
                    "total_debit_alternate" : trial_balance.total_debit_alternate,
                    "total_credit_alternate" : trial_balance.total_credit_alternate,
                    "total_currency" : trial_balance.balance_debit_alternate - trial_balance.balance_credit_alternate,
                    "contract" : trial_balance.contract.code if trial_balance.contract else "",
                })
        #return sorted(lease_dict, key=lambda x: x["leases"]["overdue_days"], reverse=True)
        return trial_balance_dict