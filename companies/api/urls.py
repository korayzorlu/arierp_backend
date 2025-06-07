from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'companies', CompanyList, "companies_api")
router.register(r'user_companies', UserCompanyList, "user_companies_api")
router.register(r'users_in_company', UsersInCompanyList, "users_in_company_api")
router.register(r'invitations', InvitationList, "invitations_api")

urlpatterns = [
    path('',include(router.urls)),
]
