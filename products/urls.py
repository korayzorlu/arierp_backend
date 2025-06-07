from django.urls import path, include

from .views import *
from .tests import *

app_name = "products"

urlpatterns = [
    path('add_category/', AddCategoryView.as_view(), name="add_category"),
    path('update_category/', UpdateCategoryView.as_view(), name="update_category"),
    path('delete_category/', DeleteCategoryView.as_view(), name="delete_category"),
    
    path('', include("products.api.urls")),
]