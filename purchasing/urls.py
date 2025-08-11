from django.urls import path, include

from .views import *
from .tests import *

app_name = "purchasing"

urlpatterns = [


    path('', include("purchasing.api.urls")),
]