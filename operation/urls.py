from django.urls import path, include

from .views import *
from .tests import *

app_name = "operation"

urlpatterns = [
    path('add_partner_advance_activity/', AddPartnerAdvanceActivityView.as_view(), name="add_partner_advance_activity"),

    path('', include("operation.api.urls")),
]