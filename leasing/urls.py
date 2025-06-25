from django.urls import path, include

from .views.lease_views import *
from .views.installments_views import *
from .tests import *

app_name = "leasing"

urlpatterns = [
    path('add_lease/', AddLeaseView.as_view(), name="add_lease"),
    path('update_lease/', UpdateLeaseView.as_view(), name="update_lease"),
    path('delete_lease/', DeleteLeaseView.as_view(), name="delete_lease"),
    path('delete_leases/', DeleteLeasesView.as_view(), name="delete_leases"),
    path('delete_all_leases/', DeleteAllLeasesView.as_view(), name="delete_all_leases"),
    path('leases_template/', LeasesTemplateView.as_view(), name="leases_template"),
    path('import_leases/', ImportLeasesView.as_view(), name="import_leases"),

    path('add_installment/', AddInstallmentView.as_view(), name="add_installment"),
    path('update_installment/', UpdateInstallmentView.as_view(), name="update_installment"),
    path('delete_installment/', DeleteInstallmentView.as_view(), name="delete_installment"),
    path('delete_installments/', DeleteInstallmentsView.as_view(), name="delete_installments"),
    path('delete_all_installments/', DeleteAllInstallmentsView.as_view(), name="delete_all_installments"),
    path('installments_template/', InstallmentsTemplateView.as_view(), name="installments_template"),
    path('import_installments/', ImportInstallmentsView.as_view(), name="import_installments"),
    
    
    path('', include("leasing.api.urls")),
]