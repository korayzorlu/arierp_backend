from django.urls import path, include

from .views.quick_quotation_views import *
from .views.quotation_views import *
from .tests import *

app_name = "quotations"

urlpatterns = [
    path('add_quick_quotation/', AddQuickQuotationView.as_view(), name="add_quick_quotation"),
    path('update_quick_quotation/', UpdateQuickQuotationView.as_view(), name="update_quick_quotation"),
    path('delete_quick_quotation/', DeleteQuickQuotationView.as_view(), name="delete_quick_quotation"),
    path('delete_quick_quotations/', DeleteQuickQuotationsView.as_view(), name="delete_quick_quotations"),
    path('delete_all_quick_quotations/', DeleteAllQuickQuotationsView.as_view(), name="delete_all_quick_quotations"),
    path('quick_quotations_template/', QuickQuotationsTemplateView.as_view(), name="quick_quotations_template"),
    path('import_quick_quotations/', ImportQuickQuotationsView.as_view(), name="import_quick_quotations"),
    
    path('', include("quotations.api.urls")),
]