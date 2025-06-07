from django.urls import path, include

from .views.account_views import *
from .views.invoice_views import *
from .views.payment_views import *

app_name = "accounting"

urlpatterns = [
    path('add_account/', AddAccountView.as_view(), name="add_account"),
    path('update_account/', UpdateAccountView.as_view(), name="update_account"),
    path('delete_account/', DeleteAccountView.as_view(), name="delete_account"),

    path('add_invoice/', AddInvoiceView.as_view(), name="add_invoice"),
    path('update_invoice/', UpdateInvoiceView.as_view(), name="update_invoice"),
    path('delete_invoice/', DeleteInvoiceView.as_view(), name="delete_invoice"),

    path('add_payment/', AddPaymentView.as_view(), name="add_payment"),
    path('update_payment/', UpdatePaymentView.as_view(), name="update_payment"),
    path('delete_payment/', DeletePaymentView.as_view(), name="delete_payment"),
    
    path('', include("accounting.api.urls")),
]