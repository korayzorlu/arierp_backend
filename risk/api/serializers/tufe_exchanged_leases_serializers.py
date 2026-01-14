from rest_framework import serializers
from rest_framework.utils import html, model_meta, representation
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery,Sum

from decimal import Decimal
from datetime import date,timedelta,datetime
from django.utils import timezone

from risk.models import *
from leasing.utils.common_utils import vendor_filter_for_serializers,max_overdue_days,total_overdue_amount,total_temerrut_amount,paid_rate,project_filter_for_serializers,processed_amount
from contracts.models import WarningNotice
from leasing.models import Installment
from trade.models import TradeTransaction
from common.models import ExchangeRate
from django.db.models.functions import TruncDate

class TufeExchangedLeaseListSerializer(serializers.Serializer):
    id = serializers.CharField(source = "uuid")
    companyId = serializers.SerializerMethodField()
    code = serializers.CharField()
    contract = serializers.SerializerMethodField()
    contract_id = serializers.SerializerMethodField()
    type = serializers.CharField()
    vat = serializers.DecimalField(max_digits=5,decimal_places=2)
    activation_date = serializers.DateField()
    lease_status = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    musteri_baz_maliyet = serializers.DecimalField(max_digits=14,decimal_places=2)
    vade = serializers.IntegerField()
    leasing_rate = serializers.DecimalField(max_digits=14,decimal_places=2)
    irr = serializers.DecimalField(max_digits=14,decimal_places=2)
    project_no = serializers.CharField()
    project_name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    leasing_type = serializers.CharField()
    application_no = serializers.CharField()
    is_last_project = serializers.BooleanField()
    current_request = serializers.CharField()
    finansman_kurum = serializers.CharField()
    is_tufe = serializers.BooleanField()
    is_musterek = serializers.BooleanField()
    bbsn = serializers.CharField()
    partner = serializers.SerializerMethodField()
    partner_tc = serializers.SerializerMethodField()
    partner_crm_code = serializers.SerializerMethodField()
    partner_special = serializers.SerializerMethodField()
    quotation = serializers.SerializerMethodField()
    kof = serializers.SerializerMethodField()
    block = serializers.SerializerMethodField()
    unit = serializers.SerializerMethodField()
    overdue_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    overdue_days = serializers.IntegerField()
    processed_amount = serializers.DecimalField(max_digits=14,decimal_places=2)
    lease_status_update_date = serializers.DateTimeField()
    terminated_date = serializers.DateField()
    #exchanged_amounts = serializers.SerializerMethodField()
    paid_rate = serializers.DecimalField(max_digits=14,decimal_places=2)
    #kur_kaybi_yuzde = serializers.SerializerMethodField()
    odenmesi_gereken_yerel = serializers.DecimalField(max_digits=14,decimal_places=2)
    odenmesi_gereken_usd = serializers.DecimalField(max_digits=14,decimal_places=2)
    odenen_yerel = serializers.DecimalField(max_digits=14,decimal_places=2)
    odenen_usd = serializers.DecimalField(max_digits=14,decimal_places=2)
    geciken_usd = serializers.DecimalField(max_digits=14,decimal_places=2)
    geciken_odenmesi_gereken_usd = serializers.DecimalField(max_digits=14,decimal_places=2)
    kur_kaybi = serializers.DecimalField(max_digits=14,decimal_places=2)
    kur_kaybi_yuzde = serializers.DecimalField(max_digits=14,decimal_places=2)
    tufeli_geciken = serializers.DecimalField(max_digits=14,decimal_places=2)
    tufe_amount = serializers.SerializerMethodField()
    tufe_rate = serializers.SerializerMethodField()
    tufe_endeks = serializers.DecimalField(max_digits=14,decimal_places=2)
    tufe_odenmesi_gereken = serializers.DecimalField(max_digits=14,decimal_places=2)
    tufe_odenen = serializers.DecimalField(max_digits=14,decimal_places=2)
    tufe_fark = serializers.DecimalField(max_digits=14,decimal_places=2)
    
    def get_companyId(self, obj):
        return obj.company.id if obj.company else ''
    
    def get_contract(self, obj):
        return obj.contract.code if obj.contract else ""
    
    def get_contract_id(self, obj):
        return obj.contract.contract_id if obj.contract else ""

    def get_currency(self, obj):
        return obj.currency.code if obj.currency else ""
    
    def get_lease_status(self, obj):
        return obj.get_lease_status_display() if obj.lease_status else ""
    
    def get_status(self, obj):
        return obj.status.name if obj.status else ""
    
    def get_partner(self, obj):
        return obj.contract.partner.name if obj.contract.partner else ""
    
    def get_partner_tc(self, obj):
        return obj.contract.partner.tc_vkn_no if obj.contract.partner else ""
    
    def get_partner_crm_code(self, obj):
        return obj.contract.partner.crm_code if obj.contract.partner else ""
    
    def get_partner_special(self, obj):
        return True if "special" in obj.contract.partner.types else False
    
    def get_quotation(self, obj):
        return obj.contract.quotation_obj.code if obj.contract.quotation_obj else ""
    
    def get_kof(self, obj):
        return obj.contract.kof if obj.contract else ""
    
    def get_project_name(self, obj):
        return obj.contract.project if obj.contract else ""
    
    def get_block(self, obj):
        return obj.contract.quotation_obj.quick_quotation.block if obj.contract.quotation_obj and obj.contract.quotation_obj.quick_quotation else ""
    
    def get_unit(self, obj):
        return obj.contract.quotation_obj.quick_quotation.unit if obj.contract.quotation_obj and obj.contract.quotation_obj.quick_quotation else ""
    
    def get_tufe_amount(self, obj):
        return obj.tufe_fark - obj.overdue_amount
    
    def get_tufe_rate(self, obj):
        return ((obj.tufeli_geciken / obj.overdue_amount if obj.overdue_amount != 0 else Decimal('1.00')) - Decimal('1.00')) * Decimal('100.00')
    
    # def get_exchanged_amounts(self, obj):
    #     installments = Installment.objects.select_related().filter(
    #         lease=obj,
    #         payment_date__lte=date.today()
    #     )

    #     installments_total = installments.aggregate(total_amount=Sum('amount'))

    #     exchanged_amount_due_to_date = Decimal('0.00')
    #     for installment in installments:
    #         exchange_rate = ExchangeRate.objects.select_related("target_currency").filter(date=installment.payment_date, target_currency__code="USD").first()
    #         exchanged_amount_due_to_date += installment.amount / exchange_rate.forex_buying if exchange_rate else installment.amount
        
    #     trade_transactions = TradeTransaction.objects.select_related().annotate(
    #         due_date_date=TruncDate('due_date')
    #     ).filter(
    #         lease=obj,
    #         posting_group_name='Kira',
    #         amount_type='0',
    #         due_date__lte=datetime.now()
    #     )

    #     trade_transactions_total = trade_transactions.aggregate(total_amount=Sum('amount'))

    #     exchanged_amount_paid_to_date = Decimal('0.00')
    #     for transaction in trade_transactions:
    #         exchange_rate = ExchangeRate.objects.select_related("target_currency").filter(date=transaction.due_date.date(), target_currency__code="USD").first()
    #         exchanged_amount_paid_to_date += transaction.amount / exchange_rate.forex_buying if exchange_rate else transaction.amount

    #     kur_kaybi_yuzde = Decimal('0.00')
    #     if exchanged_amount_due_to_date != Decimal('0.00'):
    #         kur_kaybi_yuzde = exchanged_amount_paid_to_date / exchanged_amount_due_to_date * Decimal('100.00')
    #     else:
    #         kur_kaybi_yuzde = Decimal('0.00')

    #     return {
    #         "odenmesi_gereken_yerel": installments_total['total_amount'] or Decimal('0.00'),
    #         "odenmesi_gereken_usd": exchanged_amount_due_to_date,
    #         "odenen_yerel": trade_transactions_total['total_amount'] or Decimal('0.00'),
    #         "odenen_usd": exchanged_amount_paid_to_date,
    #         "geciken_usd":  obj.overdue_amount / (ExchangeRate.objects.select_related("target_currency").filter(date=date.today(), target_currency__code="USD").first().forex_buying if ExchangeRate.objects.select_related("target_currency").filter(date=date.today(), target_currency__code="USD").first() else Decimal('1.00')),
    #         "geciken_odenmesi_gereken_usd" : exchanged_amount_due_to_date - exchanged_amount_paid_to_date,
    #         "kur_kaybi" : exchanged_amount_due_to_date - exchanged_amount_paid_to_date - (obj.overdue_amount / (ExchangeRate.objects.select_related("target_currency").filter(date=date.today(), target_currency__code="USD").first().forex_buying if ExchangeRate.objects.select_related("target_currency").filter(date=date.today(), target_currency__code="USD").first() else Decimal('1.00'))),
    #         "kur_kaybi_yuzde" : kur_kaybi_yuzde
    #     }
    
    # def get_kur_kaybi_yuzde(self, obj):
    #     installments = Installment.objects.select_related().filter(
    #         lease=obj, 
    #         payment_date__lte=date.today()
    #     )

    #     exchanged_amount_due_to_date = Decimal('0.00')
    #     for installment in installments:
    #         exchange_rate = ExchangeRate.objects.select_related("target_currency").filter(date=installment.payment_date, target_currency__code="USD").first()
    #         exchanged_amount_due_to_date += installment.amount / exchange_rate.forex_buying if exchange_rate else installment.amount

    #     trade_transactions = TradeTransaction.objects.select_related().annotate(
    #         due_date_date=TruncDate('due_date')
    #     ).filter(
    #         lease=obj,
    #         posting_group_name='Kira',
    #         amount_type='0',
    #         due_date__lte=datetime.now()
    #     )

    #     exchanged_amount_paid_to_date = Decimal('0.00')
    #     for transaction in trade_transactions:
    #         exchange_rate = ExchangeRate.objects.select_related("target_currency").filter(date=transaction.due_date.date(), target_currency__code="USD").first()
    #         exchanged_amount_paid_to_date += transaction.amount / exchange_rate.forex_buying if exchange_rate else transaction.amount

    #     kur_kaybi_yuzde = Decimal('0.00')
    #     if exchanged_amount_due_to_date != Decimal('0.00'):
    #         kur_kaybi_yuzde = exchanged_amount_paid_to_date / exchanged_amount_due_to_date * Decimal('100.00')
    #     else:
    #         kur_kaybi_yuzde = Decimal('0.00')

    #     return kur_kaybi_yuzde