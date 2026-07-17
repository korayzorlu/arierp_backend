from django.urls import path, include
from rest_framework import routers

from .views import *

router = routers.DefaultRouter()
router.register(r'kapama_detaylari',KapamaDetayList, "kapama_detaylari_api")
router.register(r'kapama_hareketleri',KapamaHareketiList, "kapama_hareketleri_api")
router.register(r'krs_reports',KrsReportList, "krs_reports_api")
router.register(r'krs_reports_cs0000',KrsReportCS0000List, "krs_reports_cs0000_api")
router.register(r'krs_reports_cs0100',KrsReportCS0100List, "krs_reports_cs0100_api")
router.register(r'krs_reports_cs0200',KrsReportCS0200List, "krs_reports_cs0200_api")
router.register(r'krs_reports_cs0301',KrsReportCS0301List, "krs_reports_cs0301_api")
router.register(r'krs_reports_cs9999',KrsReportCS9999List, "krs_reports_cs9999_api")

urlpatterns = [
    path('',include(router.urls)),
]
