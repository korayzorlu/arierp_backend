from django.urls import path, include

from .views import *
from .tests import *

app_name = "finance"

urlpatterns = [
    
    path('', include("finance.api.urls")),
]