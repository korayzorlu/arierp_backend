from django.urls import path, include

from .views import *
from .tests import *

app_name = "ledger"

urlpatterns = [
    
    path('', include("ledger.api.urls")),
]