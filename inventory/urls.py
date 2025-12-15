from django.urls import path, include

from .views import *
from .tests import *

app_name = "inventory"

urlpatterns = [


    path('', include("inventory.api.urls")),
]