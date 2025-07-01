from django.urls import path, include

from .views import *
from .tests import *

app_name = "trade"

urlpatterns = [
    
    path('', include("trade.api.urls")),
]