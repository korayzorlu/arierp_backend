from django.urls import path, include

from .views import *
from .tests import *

app_name = "projects"

urlpatterns = [


    path('', include("projects.api.urls")),
]