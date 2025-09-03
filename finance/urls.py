from django.urls import path, include

from .views import *
from .tests import *

app_name = "finance"

urlpatterns = [
    path('add_bank_activity/', AddBankActivityView.as_view(), name="add_bank_activity"),
    path('finance_summary/', FinanceSummaryView.as_view(), name="finance_summary"),

    path('', include("finance.api.urls")),
]