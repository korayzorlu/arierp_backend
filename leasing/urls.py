from django.urls import path, include

from .views import *
from .tests import *

app_name = "leasing"

urlpatterns = [
    
    path('', include("leasing.api.urls")),
]