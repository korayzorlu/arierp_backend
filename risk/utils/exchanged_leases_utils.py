from django.db.models.functions import TruncDate
from django.db.models import QuerySet, Q,Max,Count,When,Case,BooleanField,Value,OuterRef, Subquery,Sum

from datetime import date, datetime
from decimal import Decimal



from leasing.models import Installment
from common.models import ExchangeRate,TufeRate
from trade.models import TradeTransaction
import traceback

def compute_exchanged_amounts(obj):
    installments = Installment.objects.select_related().filter(
        lease=obj,
        payment_date__lte=date.today()
    )
    installments_total = installments.aggregate(total_amount=Sum('amount'))

    exchanged_amount_due_to_date = Decimal('0.00')
    for inst in installments:
        rate = ExchangeRate.objects.select_related("target_currency").filter(
            date=inst.payment_date, target_currency__code="USD"
        ).first()
        exchanged_amount_due_to_date += inst.amount / rate.forex_buying if rate else inst.amount

    trade_transactions = TradeTransaction.objects.select_related().annotate(
        due_date_date=TruncDate('due_date')
    ).filter(
        lease=obj,
        posting_group_name='Kira',
        amount_type='0',
        due_date__lte=datetime.now()
    ).exclude(delete_status__in=['2'])
    trade_transactions_total = trade_transactions.aggregate(total_amount=Sum('amount'))

    exchanged_amount_paid_to_date = Decimal('0.00')
    for tr in trade_transactions:
        rate = ExchangeRate.objects.select_related("target_currency").filter(
            date=tr.due_date.date(), target_currency__code="USD"
        ).first()
        exchanged_amount_paid_to_date += tr.amount / rate.forex_buying if rate else tr.amount

    today_rate = ExchangeRate.objects.select_related("target_currency").filter(
        date=date.today(), target_currency__code="USD"
    ).first()
    usd_div = today_rate.forex_buying if today_rate else Decimal('1.00')

    return {
        "odenmesi_gereken_yerel": installments_total['total_amount'] or Decimal('0.00'),
        "odenmesi_gereken_usd": exchanged_amount_due_to_date,
        "odenen_yerel": trade_transactions_total['total_amount'] or Decimal('0.00'),
        "odenen_usd": exchanged_amount_paid_to_date,
        "geciken_usd": obj.overdue_amount / usd_div,
        "geciken_odenmesi_gereken_usd": exchanged_amount_due_to_date - exchanged_amount_paid_to_date,
        "kur_kaybi": exchanged_amount_due_to_date - exchanged_amount_paid_to_date - (obj.overdue_amount / usd_div),
    }

def compute_tufe_endeks(obj):
    installments = Installment.objects.select_related().filter(
        lease=obj,
        payment_date__lte=date.today()
    )

    tufe_endeks = Decimal('0.00')
    for installment in installments:
        tufe_rate = TufeRate.objects.select_related().filter(date__year=installment.payment_date.year, date__month=installment.payment_date.month - 1).first()
        tufe_endeks += installment.amount / tufe_rate.value if tufe_rate else installment.amount

    return tufe_endeks

def compute_tufe_ana_endeks(obj):
    installments = Installment.objects.select_related().filter(
        lease=obj,
        payment_date__lte=date.today()
    )

    tufe_ana_endeks = Decimal('0.00')
    sum_installment_amounts = Decimal('0.00')
    sum_tufe_values = Decimal('0.00')
    for installment in installments:
        tufe_rate = TufeRate.objects.select_related().filter(date__year=installment.payment_date.year, date__month=installment.payment_date.month - 1).first()
        sum_installment_amounts = sum_installment_amounts + installment.amount
        sum_tufe_values = sum_tufe_values + (tufe_rate.value if tufe_rate else Decimal('1.00'))
    
    tufe_ana_endeks = sum_installment_amounts / sum_tufe_values if sum_tufe_values != Decimal('0.00') else Decimal('0.00')

    return tufe_ana_endeks