from django.urls import path, include
from . import views

app_name = 'compliance'

urlpatterns = [
    path('add_black_list_person/', views.AddBlackListPersonView.as_view(), name="add_black_list_person"),
    
    path('update_third_person_status/', views.UpdateThirdPersonStatusView.as_view(), name="update_third_person_status"),

    path('', include("compliance.api.urls")),
]