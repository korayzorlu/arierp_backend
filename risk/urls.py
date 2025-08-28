from django.urls import path, include

from .views import *
from .tests import *

app_name = "risk"

urlpatterns = [

    path('', include("risk.api.urls")),
]