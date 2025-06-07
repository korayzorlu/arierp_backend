from django.urls import path, include

from .views import *

app_name = "companies"

urlpatterns = [
    path('add_company/', AddCompanyView.as_view(), name="add_company"),
    path('update_company/', UpdateCompanyView.as_view(), name="update_company"),
    path('delete_company/', DeleteCompanyView.as_view(), name="delete_company"),

    path('update_user_company/', UpdateUserCompanyView.as_view(), name="update_user_company"),
    path('delete_user_company/', DeleteUserCompanyView.as_view(), name="delete_user_company"),
    
    path('add_invitation/', AddInvitationView.as_view(), name="add_invitation"),
    path('confirm_invitation/', ConfirmInvitationView.as_view(), name="confirm_invitation"),

    path('display_currency_settings/', DisplayCurrencySettingsView.as_view(), name="display_currency_settings"),
    
    path('api/', include("companies.api.urls")),
]