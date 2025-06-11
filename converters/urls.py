from django.urls import path, include

from .views.banka_tahsilati_views import *
from .views.banka_tahsilati_odoo_views import *
from .tests import *

app_name = "converters"

urlpatterns = [
    path('delete_banka_tahsilati/', DeleteBankaTahsilatiView.as_view(), name="delete_banka_tahsilati"),
    path('delete_banka_tahsilatlari/', DeleteBankaTahsilatlariView.as_view(), name="delete_banka_tahsilatlari"),
    path('delete_all_banka_tahsilatlari/', DeleteAllBankaTahsilatlariView.as_view(), name="delete_all_banka_tahsilatlari"),
    path('import_banka_tahsilatlari/', ImportBankaTahsilatlariView.as_view(), name="import_banka_tahsilatlari"),

    path('delete_banka_tahsilati_odoo/', DeleteBankaTahsilatiOdooView.as_view(), name="delete_banka_tahsilati_odoo"),
    path('delete_banka_tahsilatlari_odoo/', DeleteBankaTahsilatlariOdooView.as_view(), name="delete_banka_tahsilatlari_odoo"),
    path('delete_all_banka_tahsilatlari_odoo/', DeleteAllBankaTahsilatlariOdooView.as_view(), name="delete_all_banka_tahsilatlari_odoo"),
    path('import_banka_tahsilatlari_odoo/', ImportBankaTahsilatlariOdooView.as_view(), name="import_banka_tahsilatlari_odoo"),
    path('fix_banka_tahsilatlari_odoo/', FixBankaTahsilatlariOdooView.as_view(), name="fix_banka_tahsilatlari_odoo"),
    
    path('', include("converters.api.urls")),
]