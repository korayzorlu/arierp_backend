from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'sectors', SectorList, "sectors_api")
router.register(r'sgk_jobs', SgkJobList, "sgk_jobs_api")
router.register(r'partners', PartnerList, "partners_api")
router.register(r'partner_notes', PartnerNoteList, "partner_notes_api")
router.register(r'partner_financial_profiles', PartnerFinancialProfileList, "partner_financial_profiles_api")
router.register(r'partner_scores', PartnerScoreList, "partner_scores_api")

urlpatterns = [
    path('',include(router.urls)),
]
