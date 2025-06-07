from django.urls import path, include

from .views import *
from .tests import *

app_name = "partners"

urlpatterns = [
    path('add_partner/', AddPartnerView.as_view(), name="add_partner"),
    path('update_partner/', UpdatePartnerView.as_view(), name="update_partner"),
    path('delete_partner/', DeletePartnerView.as_view(), name="delete_partner"),
    path('delete_partners/', DeletePartnersView.as_view(), name="delete_partners"),
    path('delete_all_partners/', DeleteAllPartnersView.as_view(), name="delete_all_partners"),
    path('partners_template/', PartnersTemplateView.as_view(), name="partners_template"),
    path('import_partners/', ImportPartnersView.as_view(), name="import_partners"),

    path('test/', ExampleView.as_view(), name="test"),
    
    path('', include("partners.api.urls")),
]