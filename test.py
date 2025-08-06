# from decimal import Decimal, ROUND_HALF_UP
# from leasing.models import Lease,Installment
import requests

# installments = Installment.objects.select_related("lease").all()
# installment_by_code = {(i.lease.lease_id, i.sequency): i for i in installments if i.lease.lease_id and i.sequency}
# obj = (installment_by_code.get(("91556",0)))

# print(obj)


url = 'http://localhost:8000/api/leasing/kizilbuk_risk_partners/?ac=899bc2f0-17d9-4067-a2a2-231b92bb9e59&format=datatables'

response = requests.get(url).json()
print(response)