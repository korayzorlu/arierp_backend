from django.urls import path, include

from .views import *
from .tests import *

app_name = "operation"

urlpatterns = [

    path('', include("operation.api.urls")),
]