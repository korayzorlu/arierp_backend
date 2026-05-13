from django.urls import path, include

from .views.partner_views import *
from .views.sector_views import *
from .tests import *

app_name = "partners"

urlpatterns = [
    path('add_sector/', AddSectorView.as_view(), name="add_sector"),
    path('update_sector/', UpdateSectorView.as_view(), name="update_sector"),
    path('delete_sector/', DeleteSectorView.as_view(), name="delete_sector"),
    path('delete_sectors/', DeleteSectorsView.as_view(), name="delete_sectors"),
    path('delete_all_sectors/', DeleteAllSectorsView.as_view(), name="delete_all_sectors"),
    path('sectors_template/', SectorsTemplateView.as_view(), name="sectors_template"),
    path('import_sectors/', ImportSectorsView.as_view(), name="import_sectors"),

    path('add_partner/', AddPartnerView.as_view(), name="add_partner"),
    path('update_partner/', UpdatePartnerView.as_view(), name="update_partner"),
    path('delete_partner/', DeletePartnerView.as_view(), name="delete_partner"),
    path('delete_partners/', DeletePartnersView.as_view(), name="delete_partners"),
    path('delete_all_partners/', DeleteAllPartnersView.as_view(), name="delete_all_partners"),
    path('partners_template/', PartnersTemplateView.as_view(), name="partners_template"),
    path('import_partners/', ImportPartnersView.as_view(), name="import_partners"),
    path('partner_information/', PartnerInformationView.as_view(), name="partner_information"),
    path('ignore_partner/', IgnoePartnerView.as_view(), name="ignore_partner"),
    path('confirm_partner/', ConfirmPartnerView.as_view(), name="confirm_partner"),

    path('export_partners/', ExportPartnersView.as_view(), name="export_partners"),
    path('partners_excel/', PartnersExcelView.as_view(), name="partners_excel"),

    path('add_partner_note/', AddPartnerNoteView.as_view(), name="add_partner_note"),
    path('update_partner_note/', UpdatePartnerNoteView.as_view(), name="update_partner_note"),
    path('delete_partner_note/', DeletePartnerNoteView.as_view(), name="delete_partner_note"),

    path('update_partner_financial_profile/', UpdatePartnerFinancialProfileView.as_view(), name="update_partner_financial_profile"),

    path('test/', ExampleView.as_view(), name="test"),
    
    path('', include("partners.api.urls")),
]