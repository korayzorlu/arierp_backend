from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery,Sum

from decimal import Decimal
from datetime import date,timedelta,datetime
from django.utils import timezone

from finance.models import *
from companies.models import Company,UserCompany
from partners.models import Partner
from leasing.models import Lease
from leasing.utils.common_utils import vendor_filter_for_serializers,max_overdue_days,total_overdue_amount,total_temerrut_amount,paid_rate,project_filter_for_serializers,processed_amount

    
class BankAccountListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    id = serializers.CharField(source='uuid')
    companyId = serializers.SerializerMethodField()
    bank_account_id = serializers.CharField()
    iban = serializers.CharField()
    account_no = serializers.CharField()
    branch_code = serializers.CharField()
    branch_name = serializers.CharField()
    finmaks_account_type = serializers.CharField()
    balance = serializers.DecimalField(max_digits=14, decimal_places=2)
    available_balance = serializers.DecimalField(max_digits=14, decimal_places=2)
    over_draft = serializers.DecimalField(max_digits=14, decimal_places=2)
    credit_risk = serializers.DecimalField(max_digits=14, decimal_places=2)
    blocked_balance = serializers.DecimalField(max_digits=14, decimal_places=2)
    credit_limit = serializers.DecimalField(max_digits=14, decimal_places=2)
    currency = serializers.SerializerMethodField()
    currency_type = serializers.CharField()
    bank_name = serializers.CharField()
    bank_code = serializers.CharField()
    bank_integration_info_id = serializers.CharField()
    last_read_time = serializers.DateTimeField()
    status = serializers.BooleanField()
    finekra_bank_account_id = serializers.CharField()
    is_active = serializers.BooleanField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_currency(self, obj):
        return obj.currency.code if obj.currency else ''

class BankAccountTransactionListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    bank_name = serializers.SerializerMethodField()
    bank_account_no = serializers.SerializerMethodField()
    bank_activity = serializers.SerializerMethodField()
    transaction_id = serializers.CharField()
    transaction_date = serializers.DateTimeField()
    explanation_field = serializers.CharField()
    description = serializers.CharField()
    amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    sender_vkn = serializers.CharField()
    sender_iban = serializers.CharField()
    sender_account_name = serializers.CharField()
    receiver_vkn = serializers.CharField()
    receiver_iban = serializers.CharField()
    receipt_number = serializers.CharField()
    value_date = serializers.DateTimeField()
    transaction_type = serializers.CharField()
    bank_code = serializers.CharField()
    balance = serializers.DecimalField(max_digits=14,decimal_places=2)
    firm_id = serializers.CharField()
    firm_name = serializers.CharField()
    firm_merchantId = serializers.CharField()
    firm_externalCode = serializers.CharField()
    transaction_branch_code = serializers.CharField()
    transaction_branch_name = serializers.CharField()
    firm_code = serializers.CharField()
    debit = serializers.CharField()
    branch_code = serializers.CharField()
    transaction_external_id = serializers.CharField()
    external_id_used = serializers.CharField()
    external_bank_id = serializers.CharField()
    reference_no = serializers.CharField()
    finmaks_process_type = serializers.CharField()
    category_name = serializers.CharField()
    integration_field_value = serializers.CharField()
    transaction_status = serializers.CharField()
    currency = serializers.SerializerMethodField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_bank_name(self, obj):
        return obj.bank_account.bank_name if obj.bank_account else ''
    
    def get_bank_account_no(self, obj):
        return obj.bank_account.account_no if obj.bank_account else ''
    
    def get_bank_activity(self, obj):
        bank_activity = obj.finmaks_transaction_bank_activities.all()
        if bank_activity:
            return True
        else:
            return False
        
    def get_currency(self, obj):
        return obj.bank_account.currency.code if obj.bank_account and obj.bank_account.currency else ''
        
class BankAccountBalanceListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    bank_account_id = serializers.CharField()
    iban = serializers.CharField()
    account_no = serializers.CharField()
    branch_code = serializers.CharField()
    branch_name = serializers.CharField()
    finmaks_account_type = serializers.CharField()
    balance = serializers.DecimalField(max_digits=14, decimal_places=2)
    available_balance = serializers.DecimalField(max_digits=14, decimal_places=2)
    over_draft = serializers.DecimalField(max_digits=14, decimal_places=2)
    credit_risk = serializers.DecimalField(max_digits=14, decimal_places=2)
    blocked_balance = serializers.DecimalField(max_digits=14, decimal_places=2)
    credit_limit = serializers.DecimalField(max_digits=14, decimal_places=2)
    currency = serializers.SerializerMethodField()
    currency_type = serializers.CharField()
    bank_name = serializers.CharField()
    bank_code = serializers.CharField()
    bank_integration_info_id = serializers.CharField()
    last_read_time = serializers.DateTimeField()
    status = serializers.BooleanField()
    finekra_bank_account_id = serializers.CharField()
    is_active = serializers.BooleanField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_currency(self, obj):
        return obj.currency.code if obj.currency else ''



class PartnerAdvanceListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()
    name = serializers.CharField()
    tc_vkn_no = serializers.CharField()
    crm_code = serializers.CharField()
    advance_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    partner_advance_activity = serializers.SerializerMethodField()
    trial_balance_amount = serializers.SerializerMethodField()
    leases = serializers.SerializerMethodField()
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_partner_advance_activity(self, obj):
        partner_advance_activity = obj.partner_partner_advance_activities.all()
        if partner_advance_activity:
            return True
        else:
            return False
        
    def get_trial_balance_amount(self, obj):
        return obj.partner_trial_balances.filter(
            Q(account_code__startswith='392.99.2.00') |
            Q(account_code__startswith='393.99.2.01')
        ).aggregate(
            total=Sum(models.F('balance_debit') - models.F('balance_credit'))
        )['total'] or Decimal('0.00')
    
    def get_leases(self, obj):
        request = self.context.get('request')
        
        leases = Lease.objects.select_related("contract","contract__partner","contract__vendor").prefetch_related("contract__contract_warning_notices").filter(
            Q(contract__partner = obj)
        ).order_by("-activation_date")

        lease_dict = {"leases": [],"total_overdue_amount": total_overdue_amount(leases), "max_overdue_days": max_overdue_days(leases) }
        if leases:
            for lease in leases:
                first_future_payment = (
                    lease.lease_installments
                    .filter(payment_date__gte=timezone.now().date())
                    .order_by('payment_date')
                    .values_list('amount', flat=True)
                    .first()
                )
                last_payment = (
                    lease.lease_installments
                    .filter()
                    .order_by('sequency')
                    .values_list('amount', flat=True)
                    .last()
                )

                lease_dict["leases"].append({
                    "id" : lease.uuid,
                    "code" : lease.code,
                    "contract" : lease.contract.code if lease.contract else "",
                    "contract_id" : lease.contract.contract_id if lease.contract else "",
                    "partner" : lease.contract.partner.name if lease.contract.partner else "",
                    "partner_tc" : lease.contract.partner.tc_vkn_no if lease.contract else "",
                    "partner_crm_code" : lease.contract.partner.crm_code if lease.contract else "",
                    "project" : lease.contract.project if lease.contract else "",
                    "block" : lease.block or "",
                    "unit" : lease.unit or "",
                    "overdue_amount" : lease.overdue_amount,
                    "overdue_days" : lease.overdue_days,
                    "currency" : lease.currency.code if lease.currency else "",
                    "lease_status" : lease.get_lease_status_display(),
                    "is_kdv_diff" : lease.is_kdv_diff,
                    "paid_rate" : lease.paid_rate,
                    "next_payment" : first_future_payment,
                    "last_payment" : last_payment,
                    "overdues" : [
                        {   
                            'id': lease.code,
                            'lease': lease.code,
                            'overdue_0_30': lease.overdue_0_30,
                            'overdue_31_60': lease.overdue_31_60,
                            'overdue_61_90': lease.overdue_61_90,
                            'overdue_91_120': lease.overdue_91_120,
                            'overdue_121_150': lease.overdue_121_150,
                            'overdue_151_180': lease.overdue_151_180,
                            'overdue_181_gte': lease.overdue_181_gte,
                        }
                    ]
                })
        return lease_dict
    
class VPosTransactionListSerializer(serializers.Serializer):
    uuid = serializers.CharField()
    companyId = serializers.SerializerMethodField()

    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
      