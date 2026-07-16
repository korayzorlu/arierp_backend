from django.urls import path, include

from .tests import *
from .views import *

app_name = "krs"

urlpatterns = [
    path('create_krs_report/', CreateKrsReportView.as_view(), name="create_krs_report"),
    path('get_krs_report_document/', GetKrsReportDocumentView.as_view(), name="get_krs_report_document"),
    
    path('', include("krs.api.urls")),
]