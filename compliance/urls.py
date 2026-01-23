from django.urls import path, include

from . import views

app_name = 'compliance'

urlpatterns = [
    path('add_black_list_person/', views.AddBlackListPersonView.as_view(), name="add_black_list_person"),
    
    path('update_third_person_status/', views.UpdateThirdPersonStatusView.as_view(), name="update_third_person_status"),
    path('import_third_person_document/', views.ImportThirdPersonDocumentsView.as_view(), name="import_third_person_document"),
    path('update_third_person_is_email_sent/', views.UpdateThirdPersonIsEmailSentView.as_view(), name="update_third_person_is_email_sent"),
    path('update_third_person_is_customer_sent/', views.UpdateThirdPersonIsCustomerSentView.as_view(), name="update_third_person_is_customer_sent"),
    path('vpos_third_persons_template/', views.VPosThirdPersonsTemplateView.as_view(), name="vpos_third_persons_template"),
    path('import_vpos_third_persons/', views.ImportVPosThirdPersonsView.as_view(), name="import_vpos_third_persons"),

    path('', include("compliance.api.urls")),
]