from trade.models import TradeTransaction
from companies.models import Company

from datetime import datetime

def make_krs_report(company, date):
    company_obj = Company.objects.filter(id = int(company)).first()
    trade_transactions = TradeTransaction.objects.select_related('lease').filter(
        company=company_obj,
        record_date__date=datetime.strptime(date, "%d.%m.%Y").date(),
        posting_group_name__in=["Kira"],
        lease__lease_status__in=["aktiflestirildi"],
    )

    if trade_transactions:
        for tt in trade_transactions:
            print(tt.lease.contract.contract_id)

    print(trade_transactions)