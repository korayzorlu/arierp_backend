from django.urls import path, include

from .views import *
from .tests import *

app_name = "purchasing"

urlpatterns = [
    path('export_purchase_payments/', ExportPurchasePaymentsView.as_view(), name="export_purchase_payments"),
    path('purchase_payments_excel/', PurchasePaymentsExcelView.as_view(), name="purchase_payments_excel"),

    path('export_purchase_documents/', ExportPurchaseDocumentsView.as_view(), name="export_purchase_documents"),
    path('purchase_documents_excel/', PurchaseDocumentsExcelView.as_view(), name="purchase_documents_excel"),

    path('', include("purchasing.api.urls")),
]