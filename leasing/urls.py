from django.urls import path, include

from .views import *
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
    
    path('', include("leasing.api.urls")),
]