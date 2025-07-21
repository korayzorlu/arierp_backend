from decimal import Decimal, ROUND_HALF_UP
from leasing.models import Lease,Installment

installments = Installment.objects.select_related("lease").all()
installment_by_code = {(i.lease.lease_id, i.sequency): i for i in installments if i.lease.lease_id and i.sequency}
obj = (installment_by_code.get(("91556",0)))

print(obj)