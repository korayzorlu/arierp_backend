from django.urls import path, include

from .views import *
from .tests import *

app_name = "projects"

urlpatterns = [
    path('export_real_estates/', ExportRealEstatesView.as_view(), name="export_real_estates"),
    path('real_estates_excel/', RealEstatesExcelView.as_view(), name="real_estates_excel"),

    path('', include("projects.api.urls")),
]