from django.urls import path, include

from .views import *
from .tests import *

app_name = "communication"

urlpatterns = [

    path('', include("communication.api.urls")),
]